# R0016 accepted-main integration: independent semantic review

## Result and authority

The exact textual merge has one concrete integration issue: two newly added Bash here-strings in `trusted_parent` reintroduce the implicit temporary-file mechanism that R0016 replaced elsewhere. The subsequently supplied corrected Bash candidate implements exactly the two-read correction recommended here. Its proposed native control is suitable for the bounded helper claim on source inspection; Apple execution remains prospective. No additional interaction defect was found in the reviewed Bash control flow or PowerShell integration regions.

This is a bounded engineering review of immutable source bytes, not an audit acceptance, native qualification, release decision, or closure. No installer or native acceptance test was executed. Syntax-only `bash -n` and inert Python AST/compile checks were performed for the proposed correction/control. Historical qualifications have not been transferred to the merged candidate. The parent retains every source-editing, native-execution, and lifecycle decision. The internal `audit-assess` skill was inspected but not applied as a formal assessment: its required governor envelope and immutable packet digest were not supplied in this task.

## Reviewed object and binding

- Repository: `/tmp/r0016-third-20261111/salah_widget`.
- Initial read-only observation: clean worktree at `d5027db7c122d88ba5c7addf5110bb381148976c`.
- Merge base: `bf566111fe530b5de2c7c63ca4586e83d5f4b965`.
- Accepted-main commit: `3b0e614114ef066de40db117d0e85c0031cf3e30`, supplied tree `ffe72c83f59e56caf035ce2a44629ad516e55ab9`.
- Trial merge tree: `fd001a041bff8decd1904027d054df45625dbfb0`.
- Input directory: `/tmp/r0016-third-20261111/work/accepted-main-integration`.
- All twelve entries in `source-bindings.json` were checked against both the supplied files and `git show <ref>:<path>` bytes. Their lengths and SHA-256 values agree.
- Relevant root `AGENTS.md` was read. No commit, push, generated-source edit, shared-source edit, branch mutation, or child delegation occurred.

| Reviewed source | Trial-merge blob | SHA-256 |
| --- | --- | --- |
| `install.sh` | `e47ba73abf82e4c2ec1219fb04ab287ff99f48a7` | `af6414e9472715d8eb6e49e8afeef2abd34bfe3afcb3a43e1eccba2de577685f` |
| `install.ps1` | `28cfdae73305a2a2e5a58e30878bffea7b5142b8` | `07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a` |

README bytes were identity-checked only. Resolution and semantic review of its merge conflict are outside this review.

## Finding I01: new B2 symlink reads bypass the R0016 no-implicit-file pattern

**Evidence:** Trial-merge `install.sh` lines 114 and 117 each contain:

```bash
IFS=: read -r dev inode owner mode <<< "$fields"
```

They appear inside the new B2 supplied-spelling walk. The first parses the symlink identity and the second parses its resolved containing-directory identity. The physical-path walk at line 131 and `verify_root` at line 159 already use R0016's process-substitution form. The source's adjacent R0016 comment at lines 83–84 explicitly identifies Apple Bash 3.2's hidden-file hazard for here-documents and here-strings.

**Reachability and effect:** `initialize_staging` calls `trusted_parent` for both TMPDIR and HOME before allocating either owned root (lines 194–199). A normal invocation, including NO_OPEN mode, reaches these reads when a supplied parent spelling includes a symlink such as the admitted operating-system `/tmp` or `/var` links on macOS. The reads can therefore perform temporary-file work before explicit owned staging is established. The first read also occurs before the link-owner rejection, and the second before the container-permission rejection, so an eventually refused symlink spelling can encounter the same mechanism. This review did not reproduce an actual Apple file creation; that remains a native acceptance obligation.

This is **not** evidence that whole-entry preview creates such files. The merged preview branch exits at line 871, before terminal acquisition at 874 and staging at 911; `initialize_staging` independently rejects DRY_RUN at line 190. The defect is the combined source's input mechanism and the read-only nature expected of parent admission, not a newly demonstrated top-level DryRun escape.

**Minimal correction:** Replace only the two reads with:

```bash
IFS=: read -r dev inode owner mode < <(printf '%s\n' "$fields")
```

The `read` builtin remains in the calling shell; only the producer runs in process substitution. The data, delimiter, `IFS`, `-r`, variables, and all subsequent checks are retained. Do not change owner/mode rules, symlink policy, or staging order to address this issue.

The exact two-replacement projection is 46,460 bytes, SHA-256 `27442c0e6a6dbd6390ba1ea9b8b3efa2bfb2a910037e2c415756f9169a5c7b3f`, Git blob ID `e2e2640eb85adf302c87305cd68d642743785bb1`. This was computed in memory only; no corrected installer was written. Any additional edits yield a different object and require their own binding.

## B2 protections retained by that correction

The merged `path_identity` is byte-identical to accepted main. On macOS it obtains `%p`, validates octal digits, and masks with `07777`, retaining sticky/set-ID permission bits without file type. The `trusted_parent` function is identical to accepted main after normalizing all three equivalent field-read redirections to the process-substitution form. Thus the proposed two-line correction preserves the following predicates and order:

- Absolute, newline-free supplied spelling; trailing slash handling; refusal of empty, dot, and dot-dot components.
- Supplied symlinks require owner UID 0 and a physically resolved containing directory owned by UID 0 with no group/other write bits. A sticky world-writable container does not qualify for this symlink exception.
- Resolution to one physical path precedes the physical component walk.
- Every physical component is a non-symlink directory owned by root or the current user; writable ancestors require root ownership and sticky mode.
- Final HOME remains owned by the current user and non-group/other-writable. Final scratch-parent admission retains the root-owned sticky-directory exception.
- `verify_root` retains the physical path, ownership, full identity, and exact mode-700 checks. `initialize_staging` continues to pass the admitted physical parents to `mktemp`.

These are source-semantic preservation findings, not claims that races or every operating-system ownership boundary have been dynamically requalified.

## PowerShell integration findings

### Accepted lexer sequence is retained

The complete `Test-StrictJson` region is byte-identical to accepted main (region SHA-256 `fac44a513a9efb3d0b26512fde027714c09dc4bf2c132c431dc6989775d88ceb`). It begins one `$lexer.Match($Json)` sequence and advances with `$tokenMatch.NextMatch()` at line 949. It retains the `\G` lexer anchor, the token-index/position check, and the final `$position -eq $Json.Length` requirement at line 1010. The obsolete fresh whole-document `Match($Json,$position)` loop is absent. No R0016 edit alters this traversal or its object-key/state-machine checks. This confirms retention of the accepted implementation; it is not a new timing or complexity benchmark.

### Parent admission and private-child ownership remain distinct

`Read-CompilerPathFacts` is byte-identical to accepted main (region SHA-256 `288bebbc4a96682665527c577941990402b1ff805b412782c8550c30c4626847`). The entire `Initialize-StagingNative` region, including embedded C# `StageNative.Read`, is likewise identical (region SHA-256 `85e2eedc7b94cd65ac8723924aeee0f99a4fcf4730475cbb1bee7fdfb3b8a708`).

Both implementations admit only current-user/SYSTEM/Administrators ownership for the final parent, in conjunction with a non-null DACL and the existing foreign-writer restrictions (`0x500d0156`). Their private-object predicates separately require the current user as owner, a protected DACL with exactly one ACE, and the current user's full-control allow ACE. They do not inherit the broadened parent-owner condition. The TrustedInstaller extension remains in ancestor trust, not final-parent/private-child trust.

Private-root and descendant use remains enforced at `Assert-OwnedStagingPath` lines 619 and 628. Newly created scratch/retained roots still require `.Private` at line 712. These conclusions cover both PowerShell bootstrap facts and native staging facts in the supplied source. No native ACL execution was performed.

### R0016 option resolution and effect boundaries are retained

The environment/default-resolved `$InstallSource` validation at lines 34–37 is byte-identical to R0016. It runs before discovery and rejects a resolved value outside ask/github/store. The attribute remains for supplied parameters.

The full whole-entry preview block is byte-identical to R0016 (region SHA-256 `52402578ba477a5a465d91a02d47ef3ee7fbf95a869121d235b15b9611469c24`). Its NoOpen diagnostics describe manual opening, ask remains unresolved, GitHub release/version/path remain unresolved, and the branch exits before `Read-Host` and `Initialize-Staging`.

`Open-TargetUrl` is byte-identical to R0016 (region SHA-256 `69df02f9d589d76eb5da19a3fc79cd9b295f371aba10bdfb49accfa5575e8525`): NoOpen returns before `Start-Process`; DryRun independently returns before it. `Copy-Text` continues to return false under DryRun. The 32 top-of-function DryRun guards found in merged PowerShell also occur unchanged in R0016, including compiler bootstrap/custody, native staging, artifact allocation/publication, network metadata/download, extraction, preset, clipboard, install/import, and cleanup. No new eager call into those guarded operations was introduced by the accepted-main deltas.

## Finding T01: existing controls do not establish absence of transient here-string files

Accepted main's `tests/install-staging-parent.py` (SHA-256 `b73b21a0224cbb7ef4e3208abdad283c545cbdb5bbde0f50c7071b47a21b763f`) is the correct existing B2 behavioral matrix. It uses real host defaults, supplied TMPDIR including trailing slash, unset TMPDIR, `/tmp`, and macOS `/private/tmp`; checks canonical physical output and a real initialize/cleanup round trip; and covers replaceable links, root-owned links in unsafe containers, ancestor owners/modes, final ownership, unsafe HOME, and a post-resolution link swap. Its assertions observe status, output, and retained/removed paths, not all transient file creation. It therefore need not fail on either here-string.

R0016's `tests/install-preview.py` (SHA-256 `6be6f8109ce0e219b1bbc124aecde8c59190fffbb5c9e490d8beffa1ecce415e`) does not call `trusted_parent` in its helper inventory (lines 862–875). Its initialize helper exits at the DryRun guard. Its Darwin sandbox intentionally permits fixture writes (lines 244–260); before/after snapshots and shell command spies do not capture an internal Bash file that is created and unlinked between observations. Its normal controls use physical fixture TMPDIR/HOME and confirm legitimate effects; they are not a no-temporary-file oracle.

### Smallest falsifiable native addition

Add one narrowly scoped Darwin read-only parent-admission probe, reusing the accepted test's exact prefix extraction and the R0016 native sandbox approach. Do not change the broad preview harness merely to force this path.

1. Run on native macOS using the actual `/bin/bash` and record its version, exact installer hash, test hash, host, and `/tmp` link/physical-parent facts. Require the expected Apple Bash 3.2 capability; a newer shell run is not this control.
2. Before launch, the parent creates the source-prefix driver and a private TMPDIR. The driver contains no here-documents/strings of its own, has BASH_ENV cleared, emits a nonce/readiness marker to captured stdout, and invokes only the actual `trusted_parent /tmp temp`. Set DRY_RUN=1 so the inherited EXIT cleanup remains inert. This is explicitly a helper probe, not whole-entry qualification.
3. Use a separately validated sandbox profile that denies all filesystem writes, including the fixture TMPDIR and `/tmp`, while allowing the process/pipe/fd operations needed to read source and communicate results. Capture stdout/stderr through parent-owned pipes. Do not reuse the general fixture-writable profile unchanged.
4. First prove the policy with a source-free shell explicit-write negative control and a source-free process-substitution read positive control under the same profile. Policy absence or startup failure is a blocked control, not product failure.
5. Require the corrected helper to complete with exit 0, return exactly the independently resolved physical `/tmp` directory, and emit no temporary-file/redirection diagnostic. The real OS symlink path exercises both changed reads without a privileged custom fixture.
6. Run two exact single-site revert mutants, one restoring each `<<<` in turn. Each must be rejected by that same oracle after the readiness boundary. Require a temp-file/redirection denial attributable to the changed site, not merely any nonzero exit. If a mutant survives, the probe has not established sensitivity. Retain the candidate and mutant bytes/hashes and raw output.

The existing full B2 parent matrix still needs to run against the final merged bytes on the required native hosts, with privilege-blocked rows reported honestly. The new helper control adds evidence about the two implicit-write sites; it does not replace that matrix or R0016's whole-entry/normal/NoOpen qualification. PowerShell accepted lexer, parent-owner/private-child, and preview controls should likewise bind final merged bytes; no PowerShell source correction is recommended by this review.

## Extension: corrected source and proposed native control

The parent subsequently supplied these frozen objects under `/tmp/r0016-third-20261111/work/combined-candidate/proposed`:

| Object | Bytes | SHA-256 |
| --- | ---: | --- |
| `install.sh` | 46,460 | `27442c0e6a6dbd6390ba1ea9b8b3efa2bfb2a910037e2c415756f9169a5c7b3f` |
| `tests/install-staging-readonly.py` | 7,604 | `cdf573290a502eb7681d78c5196ca9c2fbdc700fc8e17654870fd15e4fef88a8` |

The corrected installer equals the independently computed projection above, byte for byte. Its complete diff against the trial-merge installer consists only of the two read redirections; no `cd`, ownership, mode, or link predicate changed. It contains no remaining `<<<` sequence. Finding I01 is therefore addressed in these proposed source bytes, subject to native execution of the control.

The control has the following concrete properties:

- It requires native Darwin `/bin/bash` 3.2, executable native sandbox-exec, and the `/tmp` symlink resolving to `/private/tmp` (lines 53–59).
- It extracts the exact installer prefix at the existing wizard boundary. Child positional arguments remain empty; the helper argument is supplied in the environment. BASH_ENV and ENV are cleared (lines 47–52, 70–84).
- Its policy denies filesystem writes, including the fixture TMPDIR, and network; the only file-write exception is data written to `/dev/null` (lines 67–69). A real shell redirection must fail with no subject change or created file (lines 114–117).
- Both the real OS-symlink spelling and the physical spelling must return exactly `/private/tmp\n`, with exit 0, no timeout, unchanged subject snapshots, and empty stderr (lines 107–121). The physical-path positive also exercises the established process-substitution reads under the same policy. A separate source-free process-substitution control is not necessary for the present pass/fail claim.
- The exact six-space spelling-walk read pattern selects the two intended sites only. Two mutants independently restore one here-string each. Each must fail the admission oracle, have nonzero exit without timeout, leave the subject unchanged, and contain the here-document diagnostic (lines 124–132). Candidate positives plus exact-site mutant differentials establish a more specific boundary than a generic failing subprocess; an extra readiness nonce is not needed for this control's current claim.
- Before/after snapshots cover the subject tree including scripts, HOME and TMPDIR. Raw binary output, decoded observations, hashes, and per-run JSON are retained outside the read-only child; final input bytes are checked against the original source (lines 31–43, 77–105, 133–140).
- Timeout handling creates a new session and sends SIGKILL to that owned process group before communicating again. No normal-return timeout can be mistaken for an accepted helper result (lines 87–109).

Although this control sets DRY_RUN=0, it only invokes `trusted_parent`, never an initializer; the exact prefix initializes WORK_ROOT to an empty string, so its EXIT cleanup returns without effects. No source-guard change is necessary. The original recommendation to use DRY_RUN=1 was one safe driver option, not a product requirement.

Inert checks independently confirmed valid Python AST/compilation, exactly two mutation anchors at installer lines 114 and 117, and syntax-only `bash -n` success for the corrected full installer, positive helper driver, and both generated single-site mutant drivers. These commands did not source or run installer code and are not native Apple acceptance. The control's English diagnostic match assumes an English native child diagnostic; the required native run should retain its locale/raw stderr in the existing acquisition evidence. No source or test redesign is recommended from this review.

Collector/workflow additions were not supplied as reviewed bytes. Their final integration and actual dispatch remain parent-owned, as do the accepted default-parent matrix and native PowerShell runs.

## Work and limits

Only source reads, Git object reads, SHA-256/byte comparisons, in-memory correction projection, inert Python AST/compile checks, and syntax-only Bash checks were performed. Artifacts were written only under this review's assigned directory. No installer was sourced or executed; no native acceptance result, release readiness, or closure is asserted. A supplementary attempt to read accepted `tests/install-staging-owner.ps1` encountered an unavailable promisor blob and a failed automatic fetch; no conclusion uses its unseen contents. Subsequent evidence reads were restricted to already available objects. This does not affect the exact source comparisons above.

The parent-owned next decision is to bind the final integrated candidate and collect the scoped native evidence required for that candidate. The proposed Bash source already contains the recommended correction. No other installer change is requested by this review.
