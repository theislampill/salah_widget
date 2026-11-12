# Implicit state machines: installer workflows

## Purpose and scope

This registry records consequential state machines that the installers implement
implicitly, through variables, files, records, traps and control flow, rather than
through a declared model. It exists so that a change to staging, artifact admission,
cleanup, preview or manual hand-off starts from the states, guards and invariants that
the source already relies on.

Scope: this registry covers only the installer workflows examined for R0015 (issue 21:
artifact transactions and staging trust) and R0016 (issue 22: dry-run as an offline,
effect-free preview), as of merged main `e4dbf91be91f7539b36297e030f86e2a0e99f54d`
(the PR 86 merge; its tree is identical to the candidate `dfff0f8f`). The installer
blobs are `install.sh` `e2e2640e` (SHA256 `27442c0e…`) and `install.ps1` `28cfdae7`
(SHA256 `07671cb9…`). Absence of
an entry is not a claim that no other implicit machine exists.

Authority rule. The state model describes allowed transitions. Execution records
establish what happened. Owner authorization determines what may be done. None of these
substitutes for the others. This document grants no execution authority and proves no
runtime behaviour.

Per-work-order contracts stay authoritative for their own obligations. This registry
links to them and does not restate them:
[R0013](docs/state-contracts/R0013.md),
[R0015](docs/state-contracts/R0015.md),
[R0015 Windows transactions](docs/r0015-artifact-transactions.md),
[R0016](docs/state-contracts/R0016.md),
[installer coordination](docs/state-contracts/installer-coordination/PLAN.md).

### Adding or changing an entry

- Give each machine a stable ID (`ISM-INST-NNN`). Never renumber or reuse an ID. Mark a
  retired entry as retired.
- Fill each field only as far as evidence supports. Omit a field rather than guess.
- Keep the three lists separate. **Observed facts** come from source reading or a cited
  record. **Hypotheses** are plausible but untraced or unexecuted. **Unknowns** are open
  questions.
- A hardening status is one of `documented`, `enforced in code`,
  `enforced and covered by tests`, `independently verified` or `unresolved`. Each status
  claim names its evidence (test file, mutant, run id or review).
- Hosted run ids are cited as their ledgers describe them. Where a run executed earlier
  installer bytes, the entry says so.
- Add a line to [Open findings](#open-findings) for anything material.

### Merged and dropped discovery targets

- Interruption and recovery is not a separate machine. It is a transition class of
  ISM-INST-004 (staging attempt) and ISM-INST-005 (compiler context).
- Transactional replacement is folded into ISM-INST-006. Every attempt publishes into a
  fresh root. No code path replaces an earlier bundle in place.
- Install-source selection is split. Option validation is in ISM-INST-001, and the
  per-target `ask` resolution is in ISM-INST-007.
- Retained-bundle lifetime is in ISM-INST-007. Root creation and identity are in
  ISM-INST-004.

---

## ISM-INST-001: Invocation options and run mode (preview effect boundary)

**Scope and purpose.** Decides whether an invocation may cause any effect beyond local,
read-only discovery and console output. Preview must be offline and effect-free. Normal
mode, including `NO_OPEN`, downloads, stages, copies to the clipboard and asks for
manual confirmation.

**Authoritative sources.**
- [`install.sh`](install.sh): option validation ~L62–64; preview branch ~L840–872.
  DRY_RUN guards in `initialize_staging` ~L190, `cleanup_staging` ~L209, `copy_text`
  ~L262, `select_asset` ~L562, `download_tablissng_asset` ~L595, `validate_asset`
  ~L626, `retain_asset` ~L638, `expand_chromium_asset` ~L655, `download_preset` ~L702,
  `install_tablissng` ~L732 and `show_import_instructions` ~L785. Preview interpreter
  selection is in `firefox_discovery_python` ~L327 (Apple shim avoidance, `-B` at
  ~L382).
- [`install.ps1`](install.ps1): `param` ~L21–30; environment-default validation ~L35;
  preview branch ~L1640–1667. Every effectful helper opens with a `$DryRun` guard, for
  example `Initialize-CompilerNative` ~L58, `Initialize-StagingNative` ~L339,
  `Get-TrustedStagingParent` ~L586, `Download-Asset` ~L1335 and `Copy-Text` ~L789.
- Contract: [R0016](docs/state-contracts/R0016.md), sections "Product behavior under
  qualification" and "Current source-bound receiving". Preview limits are in the
  [R0015 Windows transactions](docs/r0015-artifact-transactions.md) contract under
  "Preview and evidence limits".
- Tests: [`tests/install-preview.py`](tests/install-preview.py),
  [`tests/install-preview.ps1`](tests/install-preview.ps1),
  [`tests/install-entry-native-composition.py`](tests/install-entry-native-composition.py),
  [`tools/qualification/installer_preview_windows_full_entry.py`](tools/qualification/installer_preview_windows_full_entry.py),
  [`tests/install-staging-readonly.py`](tests/install-staging-readonly.py).

**Independent dimensions.**
1. Mode: preview (`DRY_RUN=1` or `-DryRun`) or normal.
2. Opening: open browser pages, or `NO_OPEN` / `-NoOpen`. This dimension is orthogonal
   to mode. In normal mode, `NO_OPEN` still downloads, stages, copies and confirms.
3. Option validity: valid, or refused before discovery.
4. Install source: `github`, `store` or `ask`. The default is `github`.
5. Host: Bash on Linux or macOS; Windows PowerShell 5.1 or PowerShell 7, run either with
   `-File` or through `irm | iex` (see ISM-INST-005).

**Transitions.**

| From | Event | Guard | To |
|---|---|---|---|
| start | Bash: `DRY_RUN`/`NO_OPEN` not 0 or 1, unknown `SALAH_INSTALL_SOURCE`, or any argument | ~L62–64 | refused, exit 1, before discovery |
| start | PS: environment-derived `InstallSource` not ask/github/store | ~L35; `ValidateSet` does not check defaults | refused (throw) before discovery |
| validated | discovery completes | n/a | targets listed (ISM-INST-002) |
| listed | preview | none | per-target plan printed. Exit 0 if at least one target is eligible, otherwise exit 1 |
| listed | normal | n/a | selection prompt (ISM-INST-002), then staging (ISM-INST-004) |
| any preview state | direct call to an effectful helper | helper's own guard | refusal (Bash `return 1`; PS throw, or `$false`/`$null` for clipboard and preset) with no usable path |

**Guards and invariants.**
- Preview returns before terminal acquisition (Bash ~L840 precedes `acquire_terminal`
  ~L874) and before any prompt, staging root, native helper load, network request,
  extraction, preset rewrite, clipboard write, browser open or cleanup.
- Suppressed helpers return no usable path. Suppressed clipboard calls return failure
  (Bash `copy_text` returns 1; PS `Copy-Text` returns `$false`).
- Remote release, version and path facts, and an unresolved `ask` choice, are reported
  as unresolved, never as resolved values.

**Effects.** Preview: local reads of browser profile directories and metadata, and
console output only. Normal: everything described in ISM-INST-004 to ISM-INST-007.

**Failure and interruption.** Preview has no staging state to recover. Bash's EXIT trap
runs during preview, but `cleanup_staging` returns immediately when `DRY_RUN=1` (~L209).
PowerShell's `Clear-OwnedScratch` sits in a `finally` that only begins after the preview
`exit` (~L1699–1741).

**Observed facts.**
- In both installers, every listed staging, admission, transport, clipboard and open
  helper carries a preview guard (source above).
- R0016 records these receipts:
  - Linux preview: run 43173749709, 45 PASS across 61 phases.
  - Native macOS: run 43173749688, all 11 suites, 248 instrument rows.
  - Windows core75 and normal18: run 43171927589.
  - Windows routes8: run 43171927350.
  - Windows full20 on both hosts: run 43220592915. PS7 passed on attempt 1. PS5.1
    passed on attempt 2. PS5.1 attempt 1 is retained as adverse evidence with 0
    installer cases.
- The R0016 final root technical decision admits the premerge evidence within those
  recorded scopes.
- R0016 records limits that remain:
  - `independentHardContainment=NOT_ACQUIRED` on Windows.
  - Global transport telemetry is null. A denied connection is a separate observation
    from proof that no connection was attempted.
  - Windows full-lifecycle before/after comparisons are unequal, because of host startup,
    profile and TEMP activity. Only the held source windows are equal.
  - On Mac, a direct-transport mutant added 41 Python-cache entries, preserved as an
    adverse delta.
- The independent security review of the exact tree is recorded in
  [R0016](docs/state-contracts/R0016.md), "Successor receiving and merge record". It
  reports that sandboxed dry-run before/after snapshots were identical and that no stub
  was invoked.
- The same review observed host-level start-up effects in a no-op baseline too. Those
  effects come from the shell, the PowerShell host or a started interpreter, and fall
  outside the installer's no-effect statements. The review assessed macOS Python
  resolution by reasoning only and did not run Apple Bash 3.2.

**Hypotheses.**
- The unequal Windows full-lifecycle comparisons are attributed to host startup and
  profile behaviour, not to installer source. R0016's held-window design supports this
  but does not prove it for every host.

**Unknowns.**
- Whether native Windows startup, profile and module-cache effects can be excluded in
  general. This is not established. R0016 records it as a limit, not as zero effects.
- Host-wide absence of network activity during preview. This is not established.

**Hardening status.**
- Source guards: `enforced and covered by tests` (`tests/install-preview.py`,
  `tests/install-preview.ps1`; clipboard-effect, false-success and null-array mutants
  per R0016).
- Preview boundary within the recorded scopes: `independently verified` (independent
  receivers and the root technical decision cited in
  [R0016](docs/state-contracts/R0016.md); runs above).
- Host-wide zero effects and transport absence: `unresolved` (recorded limits above).
- Environment-default source validation: `enforced and covered by tests` (R0016 full20
  "resolved-source/NoOpen regressions", run 43220592915).

---

## ISM-INST-002: Discovery knowledge, target eligibility and selection

**Scope and purpose.** Decides which browser profiles may reach any effectful branch.
R0013 owns this machine. R0015 and R0016 consume its result.

**Authoritative sources.**
- [`install.sh`](install.sh): `firefox_status` ~L361, `discovery_eligibility` ~L470,
  `add_target` ~L500 (delimiter rejection), `detect_targets` ~L515, selection ~L876–910
  and dispatch re-derivation ~L922.
- [`install.ps1`](install.ps1): `Get-ChromiumExtensionStatus` ~L896, `Test-StrictJson`
  ~L942, `Get-FirefoxExtensionStatus` ~L1014, `Get-DiscoveryEligibility` ~L1091,
  `Get-Targets` ~L1102, selection ~L1670–1698 and dispatch re-derivation ~L1707.
- Contract: [R0013](docs/state-contracts/R0013.md), section "Selection, preview and
  handoff".
- Tests: [`tests/install-discovery.py`](tests/install-discovery.py),
  [`tests/install-discovery.ps1`](tests/install-discovery.ps1),
  [`tests/install-discovery-mutations.py`](tests/install-discovery-mutations.py),
  [`tests/install-entry-bash.py`](tests/install-entry-bash.py),
  [`tests/install-entry-held.ps1`](tests/install-entry-held.ps1).

**Independent dimensions.** These are kept separate, not collapsed into one status.
1. Knowledge: `known-new`, `known-neither`, `known-legacy`, `known-both` or `unknown`.
   An `unknown` carries a reason, for example `no-profile`, `profile-unavailable`,
   `metadata-absent`, `metadata-unreadable`, `metadata-encoding`, `metadata-malformed`,
   `metadata-unsupported`, `parser-unavailable`, `parser-failed` or
   `profile-path-unsupported`.
2. Legacy flag (`has_old` / `HasLegacyTabliss`). This flag overrides knowledge.
3. Derived eligibility: `eligible-known`, `unknown-held` or `legacy-refused`.
4. Selection membership: `all`, or an explicit index list.
5. Bash only: a record rejected for a delimiter or newline. It gets no index, cannot be
   selected, and is counted as held only under `all`.

**Transitions and guards.**

| Event | Bash | PowerShell |
|---|---|---|
| Legacy evidence, or `known-legacy`/`known-both` | `legacy-refused` | `legacy-refused` |
| `known-new`/`known-neither` with no legacy flag | `eligible-known` | `eligible-known` |
| Anything else | `unknown-held` | `unknown-held` |
| Empty selection | `all` | `all` |
| Malformed token, leading/trailing/double comma, or unknown index | refused, exit 1, before staging (~L882–891) | the token is silently dropped; if nothing remains, "No valid targets selected", exit 1 (~L1677–1684) |
| Duplicate index | de-duplicated | de-duplicated (membership filter) |
| Zero eligible selected targets | exit 1 before staging (~L910) | exit 1 before staging (~L1695) |
| Dispatch of each target | eligibility re-derived; held and refused targets skipped | same |

**Invariants.**
- A held or refused target never reaches staging initialization, download, extraction,
  clipboard, browser opening or preset dispatch.
- Independently eligible peers remain usable.
- Unknown is never treated as verified absence.

**Observed facts.**
- One derived predicate per host serves preview, pre-staging counting and dispatch
  (source above).
- R0013 records the Windows rows as re-acquired in run 43146668695 (attempt 2, all 11
  suites).
- Bash Chromium discovery checks only the `Extensions/<id>` directories. PowerShell also
  reads `Preferences` `extensions.settings`.

**Hypotheses.**
- A legacy Tabliss loaded through "Load unpacked" has a path-derived ID, not the store
  ID. If so, neither detector sees it, and the profile is classified `known-neither`
  (eligible). This is untested here.

**Unknowns.**
- Whether issue 19 row 19-03's strict-selection wording is meant to bind PowerShell. The
  recorded row cites only `install.sh`. PowerShell's lenient token handling cannot
  dispatch held or refused targets.

**Hardening status.**
- Eligibility gating on both hosts: `enforced and covered by tests` (tests above; run
  43146668695; the discovery mutants recorded in [R0013](docs/state-contracts/R0013.md)).
- PowerShell strict selection: `unresolved` (divergence; see Open findings).

---

## ISM-INST-003: Staging-parent trust decision

**Scope and purpose.** Decides whether a parent directory may hold a private root. On
POSIX it decides for the scratch parent (`TMPDIR`, or `/tmp`) and the retained parent
(`HOME`). On Windows it decides for `%TEMP%` and `%USERPROFILE%` staging, and separately
for the compiler's native temporary path.

**Authoritative sources.**
- [`install.sh`](install.sh): `trusted_parent` ~L97–150 and `path_identity` ~L87.
- [`install.ps1`](install.ps1): `Get-TrustedStagingParent` ~L585, which calls
  `StageNative.RequireLocalAclVolume` ~L464 and `StageNative.Read` ~L493. Compiler
  parent: `New-StagingCompilerContext` ~L167 and `Read-CompilerPathFacts` ~L91.
- Contracts: [R0015](docs/state-contracts/R0015.md), "Installer corrections round (B1,
  B2, section B controls)"; [R0015 Windows transactions](docs/r0015-artifact-transactions.md),
  "Ownership boundary".
- Tests: [`tests/install-staging-parent.py`](tests/install-staging-parent.py),
  [`tests/install-linux-owner.py`](tests/install-linux-owner.py),
  [`tests/install-staging-owner.ps1`](tests/install-staging-owner.ps1),
  [`tests/install-staging-windows.ps1`](tests/install-staging-windows.ps1),
  [`tests/install-volume-policy.ps1`](tests/install-volume-policy.ps1),
  [`tests/install-volume-mutations.py`](tests/install-volume-mutations.py).

**Independent dimensions.**
1. Spelling validity. POSIX: the path is absolute, has no newline, and has no empty,
   `.` or `..` component. Windows: a drive-letter path with no control characters,
   colons or ambiguous trailing spaces or dots.
2. Link admission. POSIX only: a symlink in the supplied spelling is admitted only if it
   is root-owned and its container is root-owned and not group- or other-writable.
3. Ancestor trust. Every component must be owned by root or the user (POSIX), or by the
   user, SYSTEM, Administrators or TrustedInstaller (Windows), with no foreign
   replacement grant.
4. Final-parent rule. Self-owned and not group- or other-writable. On POSIX, a
   root-owned sticky directory is allowed for scratch only. On Windows, the owner may be
   the user, SYSTEM or Administrators, and the DACL may grant no other writer.
5. Volume. Windows only: local, NTFS, with persistent ACLs.
6. Physical identity. POSIX resolves once with `pwd -P` and re-verifies. Windows compares
   the final handle path for aliasing and leases every component.

**Transitions.** The decision is a single pass: `spelling-checked → links-checked →
resolved → ancestors-walked → final-rule → admitted | refused`. Any failure refuses, and
initialization then fails. Bash reports "Automatic staging is unavailable…" and exits 1
(~L911). PowerShell throws inside the `try` at ~L1699.

**Authorized actors and ownership.** Only the invoking user's own token. Administrators
and processes already running as the same user are outside the isolation claim (see
[R0015 Windows transactions](docs/r0015-artifact-transactions.md)).

**Invariants.**
- No fallback to a shared directory.
- On POSIX, everything after resolution inspects only the physical path.
- On Windows, the ancestor leases stay open for the whole attempt.

**Observed facts.**
- B1 and B2 are described in [R0015](docs/state-contracts/R0015.md).
- In run 43162309006, at installer SHA256 `288d8ba1…` and `4d1818f8…`:
  - Windows owner controls passed 50/50 per host, and the owner mutants were 4/4 killed.
  - Real default `USERPROFILE` and `TEMP` were admitted on windows-2022 and
    windows-2025.
  - Every default `TMPDIR` candidate was admitted on macos-15 and ubuntu-24.04.
- On the previous Bash bytes, run 43158222646 shows the macOS default-environment
  positives failing.
- Delta against accepted main `3b0e6141`, from `git diff`:
  - The PowerShell staging and trust functions are textually unchanged.
  - Bash `trusted_parent` and `verify_root` changed only from here-strings to process
    substitution.
- The R0015 suites were re-run on the R0016 installer bytes at head `dfff0f8f`:
  - Run 43239081990 is green on Linux and on windows-2022 and windows-2025, including
    the owner/archive controls, the default-environment gates and the standard-user
    observation. `environment-posix (macos-15)` was green on attempt 3.
  - Run 43239087955 passed the staging-parent suite on ubuntu-24.04 and macos-15.
  - Both runs are recorded in [R0016](docs/state-contracts/R0016.md), "Successor
    receiving and merge record".
- `posix (macos-15, Darwin)` in run 43239081990 never acquired a runner, and that run's
  overall conclusion is failure. The macOS native staging suite was therefore not re-run
  on these bytes, and it still rests on earlier-byte evidence plus the delta above.
- The Windows staging parent (`$env:TEMP`) and the compiler parent
  (`[IO.Path]::GetTempPath()`, which prefers `TMP`) are read from different sources.
  Each is admitted independently.

**Hypotheses.**
- A root-created link to a physical name that contains a newline passes the
  supplied-spelling newline check. R0015 records this as theoretical and root-only.

**Unknowns.**
- Domain-joined, roaming and Windows 10 profiles, recorded as NOT DONE in R0015.
- macOS extended ACLs. The mode-only checks do not consider them (pre-existing, NOT
  DONE).

**Hardening status.**
- B1/B2 final-parent rules: `independently verified` for bytes `288d8ba1`/`4d1818f8`
  (run 43162309006; independent reviews of `852d026c` recorded in R0015).
- Same rules on the merged bytes: `enforced and covered by tests`. Re-run in 43239081990
  (Windows owner controls; default environments on Linux, Windows and macos-15) and
  43239087955. The macOS native staging suite was not re-run.
- Private-child owner term (`$private` / `privateAcl` require owner = user):
  `enforced in code`. R0015 records that no mutant pins it.
- Refusal-message wording ("not owned by this user"): `unresolved`. It under-describes
  the admitted owner set (see Open findings).
- The transaction contract's former "self-owned immediate parent" sentence: corrected in
  [the R0015 Windows transactions contract](docs/r0015-artifact-transactions.md) to state
  the current rule; now `documented`.

---

## ISM-INST-004: Private staging attempt (roots, identity, cleanup, interruption)

**Scope and purpose.** Governs the per-invocation pair of private roots. The scratch
root is transient and deleted after identity checks. The retained bundle root persists
for manual use. This machine also governs what cleanup may delete.

**Authoritative sources.**
- [`install.sh`](install.sh): `initialize_staging` ~L189, `verify_root` ~L152,
  `guard_owned_path` ~L165, `cleanup_staging` ~L208, `finish_installer` ~L214, and the
  traps ~L221–223. The `WORK_ROOT`, `WORK_ID`, `BUNDLE_ROOT` and `BUNDLE_ID` globals are
  set at ~L40–41.
- [`install.ps1`](install.ps1): `Initialize-Staging` ~L693, `Assert-OwnedStagingPath`
  ~L608, `Clear-OwnedScratch` ~L727, and the `try`/`finally` around dispatch
  ~L1699–1741.
- Contracts: [R0015](docs/state-contracts/R0015.md) and
  [R0015 Windows transactions](docs/r0015-artifact-transactions.md), "Manual files and
  lifetime".
- Tests: [`tests/install-bash.py`](tests/install-bash.py),
  [`tests/install-staging-native.py`](tests/install-staging-native.py) (exit, failure,
  INT and TERM boundaries), [`tests/install-mutations.py`](tests/install-mutations.py),
  [`tests/install-powershell-transactions.ps1`](tests/install-powershell-transactions.ps1),
  [`tests/install-staging-windows.ps1`](tests/install-staging-windows.ps1).

**Independent dimensions.**
1. Attempt status. Bash: unset, then initialized. PS `StagingAttempt.Status`:
   `initializing`, `active`, `initialization-failed` or `closed`.
2. Scratch root: absent, created and unverified, verified, or deleted or retained.
3. Retained root: absent, created and unverified, or verified. It is never deleted by
   the installer.
4. Leases (PS): ancestor and root handles, live or disposed.
5. Exit cause: normal exit, failure status, INT (130), TERM (143), or uncatchable
   termination.

**Transitions.**

| From | Event | Guard | To / effect |
|---|---|---|---|
| unset | eligible selection confirmed | trust admitted (ISM-INST-003); Bash requires DRY_RUN=0 and runs once; PS throws if an attempt already exists (~L695) | exclusive creation (Bash `mktemp -d` under umask 077; PS `CreateDirectoryW` with a protected DACL at creation), then identity readback |
| created | identity readback fails | n/a | Bash: initialization fails, cleanup refuses deletion, and the root is retained with a warning. PS: `initialization-failed`, leases disposed, cleanup skipped and retained |
| verified | each write | `guard_owned_path` / `Assert-OwnedStagingPath` re-verify root identity and each component | write proceeds, or refusal |
| active | normal end, failure or INT/TERM | Bash: the EXIT trap fires after INT/TERM is converted to an exit; PS: `finally` | scratch is deleted only if the root identity matches (Bash: `verify_root` then `rm -rf`; PS: every descendant private, plus identity, then `Directory.Delete`). Otherwise it is retained with a warning. The retained root is always kept |
| non-zero exit with a bundle | `finish_installer` | n/a | "Partial bundle retained; manual actions remain pending" |
| closed | cleanup invoked again | PS: the `closed` status returns early (~L730) | no-op |
| any | SIGKILL, host or window termination | no handler can run | scratch (and possibly partial candidates) remain in the temporary parent |

**Invariants.**
- Each invocation creates new roots with random names. No earlier root is ever adopted,
  reset or recursively removed.
- Cleanup deletes only the current scratch root after proving its identity.
- The retained root is never deleted by the installer.

**Observed facts.**
- Each invocation's root names are unique: `mktemp -d` templates in Bash, and the
  attempt GUID in PS (~L705–706).
- Bash `verify_root` checks the root's device, inode, owner and mode 0700, but not its
  descendants. `rm -rf` does not follow symlinks.
- PS `Clear-OwnedScratch` walks every descendant through `Get-OwnedStagingFiles` before
  deleting. It releases only the scratch root's own lease first.
- R0015 records that native Apple staging passed nine controls, including INT/TERM
  cleanup (on earlier Bash bytes).
- In run 43162309006, Windows transactions passed 28/28 and staging custody 8/8 per host.
- The R0015 suites were re-run on the R0016 bytes in run 43239081990 (attempt 3): the
  Linux posix job and both Windows jobs were green. The `posix (macos-15, Darwin)` job,
  which carries the Apple native staging and lifetime suite, never acquired a runner. The
  Apple INT/TERM evidence therefore still binds earlier Bash bytes.
- `trap` covers EXIT, INT and TERM only (~L221–223).

**Hypotheses.**
- A signal that arrives between `mktemp -d` returning and the assignment to `WORK_ROOT`
  or `BUNDLE_ROOT` leaves an unrecorded empty root. PowerShell has the analogous window
  between `New-PrivateStagingDirectory` and assignment to `StagingAttempt.Scratch`: its
  `finally` would see `initializing` and retain the root, without naming its path. This
  is untested.
- Bash probably runs the EXIT trap when it is terminated by an untrapped SIGHUP (a closed
  terminal). This is not covered by a cited test.

**Unknowns.**
- Leakage after SIGKILL or a closed console. A kill cannot run cleanup. Leaked scratch is
  never adopted by a later run, because names are fresh, but nothing reports or removes
  it. This registry found no NOT DONE record for it in the R0015 ledger.
- Behaviour when INT arrives during the EXIT trap itself (re-entrancy during `rm -rf`).

**Hardening status.**
- Freshness, confinement and identity-checked cleanup: `enforced and covered by tests`
  (`tests/install-bash.py`, `tests/install-staging-native.py`,
  `tests/install-mutations.py` predictable-root and retained-EXIT-deletion mutants; PS
  transactions and custody in run 43162309006). The Bash rows 21-04, 21-09, 21-10 and
  21-14 in issue 21 carry SATISFIED audit verdicts on earlier bytes.
- Kill-time and interrupt-window leakage: `unresolved` (documented here only).

---

## ISM-INST-005: Windows native helper compile and load

**Scope and purpose.** Decides whether the native staging helper type may be compiled
and loaded, and where the compiler may write. Every trust decision in ISM-INST-003,
ISM-INST-004 and ISM-INST-006 runs inside the loaded `SalahInstaller.StageNative` type.

**Authoritative sources.**
- [`install.ps1`](install.ps1): `Initialize-CompilerNative` ~L57 (in-memory P/Invoke
  emit), `New-StagingCompilerContext` ~L167, `Invoke-StagingCompiler` ~L262 (PS5.1
  `csc.exe` through `Diagnostics.Process`; PS7 `Add-Type`), `Clear-StagingCompilerContext`
  ~L228, and `Initialize-StagingNative` ~L338 (type check ~L341, TEMP/TMP redirect and
  restore ~L343–559).
- Contract: [R0015 Windows transactions](docs/r0015-artifact-transactions.md),
  "Ownership boundary"; history in [R0015](docs/state-contracts/R0015.md).
- Tests: [`tests/install-compiler-custody.ps1`](tests/install-compiler-custody.ps1),
  [`tests/install-staging-first-call.ps1`](tests/install-staging-first-call.ps1),
  [`tests/install-volume-policy.ps1`](tests/install-volume-policy.ps1).

**Independent dimensions.**
1. Session type state: whether `SalahInstaller.StageNative` and
   `SalahInstaller.CompilerNative` are already loaded in this process.
2. Compiler context status (`$script:CompilerScratch.Status`): `parent-admission`,
   `candidate`, `owned`, `compiling`, `compiled` or `closed`. Retained outcomes are
   `refused-before-create`, `retained-unproved`, `retained-compilation-failed` and
   `retained-cleanup-failed`.
3. Process environment: TEMP and TMP are redirected to the context and then restored,
   including the originally absent state.

**Transitions.**

| From | Event | Guard | To |
|---|---|---|---|
| type absent | first staging | parent and ancestors admitted, NTFS, token default owner is the user or Administrators | `owned` (exclusive private root and lease) |
| `owned` | compile | TEMP/TMP equal the context path, root empty, invocation not yet started | `compiling`, then `compiled`, then `closed` (verified deletion) |
| `compiling` | compiler failure or timeout | n/a | `retained-compilation-failed` (material kept, location reported) |
| `compiled` | cleanup proof fails | n/a | `retained-cleanup-failed` |
| creation succeeded, readback failed | n/a | n/a | `retained-unproved` |
| type present | any later staging in the same process | `-as [type]` succeeds (~L341) | compilation skipped. The existing type is used without re-verification |

**Invariants.**
- No compiler write precedes parent custody.
- A retained context is never an admitted artifact or bundle.

**Observed facts.**
- The R0015 sixth attempt (run 43028305607) and run 43162309006 report the compiler
  custody suites passing on both hosts. In run 43162309006, the helper compiled under the
  real TEMP on windows-2022 and windows-2025, and under a temporary standard user (a
  non-gating job).
- The README's primary Windows route is `irm … | iex`, which runs in the caller's
  session. A loaded type therefore persists after the run, and any later run in that
  session reuses it (~L341, ~L60–61).
- If compilation fails before `Invoke-StagingCompiler` starts, for example when
  `Add-Type -AssemblyName System.IO.Compression` throws, the context is still labelled
  `retained-compilation-failed`.

**Hypotheses.**
- After the script changes, a later `iex` run in the same session would use the trust
  predicates compiled by the earlier run, so the reused helper could be stale. A type of
  the same name defined by other code in the session would also be trusted. That code
  already runs as the same user, outside the isolation claim.
- Under `iex`, the script's `exit` statements end the hosting session. This is standard
  PowerShell semantics, not observed here.

**Unknowns.**
- Whether issue 20 (R0014) host obligations cover repeated `iex` invocation. Not
  examined.
- Cold-start compiler TEMP effects on hosts other than the qualified runners.

**Hardening status.**
- Compiler custody and environment confinement: `independently verified` for the native6
  scope (run 43028305607; the native6 receiving review in
  [R0015](docs/state-contracts/R0015.md)), and re-run green in 43162309006 on later bytes.
- Session-persistent type reuse: `unresolved` (documented here only).

---

## ISM-INST-006: Artifact admission and publication

**Scope and purpose.** Decides when downloaded or derived bytes become a ready artifact
that may be shown, copied or handed to a browser. The artifacts are the extension
ZIP/XPI, the unpacked Chromium tree and the configured preset.

**Authoritative sources.**
- [`install.sh`](install.sh): `download_tablissng_asset` ~L593, `validate_asset` ~L625,
  `retain_asset` ~L637, `expand_chromium_asset` ~L654 and `download_preset` ~L701.
- [`install.ps1`](install.ps1): `New-ArtifactRecord` ~L1182, `Download-Asset` ~L1334,
  `Test-ExtensionArchive` ~L1245, `StageNative.ReadZipCrcs` ~L429 and `Fingerprint`
  ~L412, `Publish-OwnedFile` ~L1195, `Get-AdmittedArtifact` ~L671,
  `Expand-ChromiumAsset` ~L1371, `Convert-ConfiguredPreset` ~L1453 and `Download-Preset`
  ~L1467.
- Contracts: [R0015 Windows transactions](docs/r0015-artifact-transactions.md), "One
  admission contract", "Supported archive checks" and "Preset schema and preservation".
- Tests: [`tests/install-bash.py`](tests/install-bash.py),
  [`tests/install-powershell-transactions.ps1`](tests/install-powershell-transactions.ps1),
  [`tests/install-archive-controls.ps1`](tests/install-archive-controls.ps1),
  [`tests/install-powershell-mutations.py`](tests/install-powershell-mutations.py).

**Independent dimensions.**
1. Record state. This is explicit in PS and implicit in Bash, where state is the file's
   location and name: a `.asset.*` or `.preset.*` partial, or the final name.
2. Byte proof: length, SHA256, ZIP CRCs, and the declared size and digest when the
   release supplies them (PS only).
3. File identity: volume and file ID in PS; root identity plus component guards in Bash.
4. Location: a scratch candidate, or a retained publication.

**PowerShell transitions** (from the contract, confirmed in source).
- Normal path: `unresolved → downloading → downloaded-unvalidated → validated →
  published → handed-off`, with `retained` at cleanup.
- Failures: `download-failed`, `validation-failed`, `publication-failed` and
  `extraction-failed` remain partial. They are never admitted.
- A same-attempt reuse whose readback has changed becomes `validation-failed`, and the
  artifact is reacquired.
- At cleanup, `published` and `handed-off` become `retained`. Any non-failed, non-retained
  record becomes `cancelled/partial-retained` (~L744–747).
- `Get-AdmittedArtifact` is the single readiness predicate. It requires a unique
  current-attempt record, current identity and unchanged bytes. For an unpacked tree it
  also requires the full file list and each file's digest.

**Bash transitions.**

| Path | Steps and outcome |
|---|---|
| Asset | Exclusive `.asset.*` partial in the scratch root; `curl`; ZIP integrity (`testzip`); rename to the final name. Failure leaves the partial in scratch, which cleanup removes |
| Same-attempt reuse | An existing final file in this attempt's fresh scratch root is revalidated before reuse (~L609–613) |
| XPI | Copied to the bundle as a partial, revalidated, then renamed. An existing bundle copy of the same name in the same attempt is reused without revalidation (~L643) |
| Chromium tree | Every member preflighted, then extracted exclusively into a new `mktemp -d` child. Failure: "partial bundle retained" |
| Preset | Partial in the bundle `presets/`; JSON validated; renamed. Failure leaves the partial in the bundle |

**Invariants.**
- No ready path before validation.
- Publication never overwrites. PS moves to a unique token name. Bash's guarded rename
  is not reached when the destination already exists.
- No cross-invocation cache adoption.
- Preview is never admitted (ISM-INST-001).

**Observed facts.**
- In run 43162309006: archive controls 9/9 and archive mutants 4/4 killed per host
  (backslash guard, digest, declared size, CRC); transaction mutations 22/22.
- R0015's native6 reviews (run 43028305607) cover 13 prerequisites and nine mutant pairs
  per host.
- On the R0016 installer bytes (head `dfff0f8f`), run 43239081990 re-ran the Windows
  transaction and owner/archive suites green on windows-2022 and windows-2025, and the
  Linux posix job green. The macOS posix job was not acquired, so Bash admission on Apple
  hosts was not re-run on these bytes.
- Bash has no declared-digest or size check and does not require an `https://` download
  URL. The R0015 Windows contract states that it does not certify the original Bash
  obligations.
- Bash `download_preset` rewrites with `str.replace('local=1', hash)` over the whole
  text. It does not validate `SALAH_WIDGET_HASH` characters, and its `read_text` and
  `write_text` normalise line endings. PowerShell rewrites only the canonical token and
  revalidates the fragment. The shipped preset contains `local=1` exactly once.

**Hypotheses.**
- A Bash `SALAH_WIDGET_HASH` containing JSON-escaped quotes could add iframe attributes
  while the result stays valid JSON. The value comes from the invoking user, or from the
  builder command the user copied. Untested.

**Unknowns.**
- Transport behaviour: timeouts, redirect scheme policy, and partial downloads during a
  slow network. R0015 records web-call timeouts as NOT DONE (section C). Bash `curl` sets
  no timeout.

**Hardening status.**
- Windows admission and publication: `independently verified` within the native6 and
  run 43162309006 scopes (R0015 ledger).
- Bash admission (rows 21-06 to 21-09): `enforced and covered by tests`
  (`tests/install-bash.py`; SATISFIED audit verdicts in issue 21 on earlier bytes).
- Bash preset rewrite scope and hash validation: `unresolved` (divergence; see Open
  findings).
- Transport hardening: `unresolved`.

---

## ISM-INST-007: Manual hand-off and retained bundle

**Scope and purpose.** Decides what the user is told and given for each eligible target,
and what the terminal summary may claim. It covers install-source resolution, clipboard
copying, page opening, acknowledgement and the retained bundle's lifetime.

**Authoritative sources.**
- [`install.sh`](install.sh): `install_tablissng` ~L731, `show_import_instructions`
  ~L784, `open_url` ~L236, `copy_text` ~L260, and the dispatch loop and summary
  ~L914–952.
- [`install.ps1`](install.ps1): `Install-TablissNG` ~L1535, `Show-ImportInstructions`
  ~L1501, `Open-TargetUrl` ~L768, `Copy-Text` ~L788, and the dispatch loop and summary
  ~L1704–1737.
- Contracts: [R0016](docs/state-contracts/R0016.md), "Product behavior under
  qualification"; [R0015 Windows transactions](docs/r0015-artifact-transactions.md),
  "Manual files and lifetime".
- Tests: [`tests/install-powershell-routes.ps1`](tests/install-powershell-routes.ps1),
  [`tests/install-entry-bash.py`](tests/install-entry-bash.py),
  [`tests/install-powershell-transactions.ps1`](tests/install-powershell-transactions.ps1).

**Independent dimensions.**
1. Resolved source per target: `store`, or `github`. `ask` is resolved by a prompt.
2. Artifact availability (ISM-INST-006).
3. Clipboard outcome: copied, or failed (best-effort).
4. Opening: opened, or `NO_OPEN`/`-NoOpen` printing the URL.
5. Acknowledgement: received, or input ended.
6. Preset: staged once per run, with a retry for the next target after a failure.
7. Terminal status: manual action pending, or nothing staged.

**Transitions.**

| Event | Bash | PowerShell |
|---|---|---|
| `ask` with an invalid choice | refused, exit 1 (~L738) | any input other than `2` selects GitHub (~L1544) |
| `store` | open or print the store URL, then ask for Enter | same |
| GitHub download or validation failure | fall back to the store page and acknowledgement | the same, inside the `try` (~L1596–1600) |
| Artifact admitted | print the path, try the clipboard, open the manager page, ask for Enter; `ASSET_STAGED=1` | admission re-checked; record set to `handed-off` after the clipboard attempt, then the page opened |
| Acknowledgement input ends | `read_answer` fails, exit 1, partial bundle retained | `Read-Host` behaviour depends on the host (see Hypotheses) |
| Summary with nothing staged | "No files were staged…", exit 1 (~L950) | prints the retained bundle path and exits 0 |

**Invariants.**
- Enter is a user acknowledgement. It never proves that a browser installed or imported
  anything.
- The retained bundle is never deleted, and is never a later run's cache.
- The dashboard-replacement warning is always shown before an import.

**Observed facts.**
- R0016 records routes8 (run 43171927350): explicit store, ask-to-store, ask-to-GitHub
  and default ask-to-GitHub, in both browser families, on both hosts, with zero fallback
  rows. The fallback scope rests on the root-admitted original18/behavior15 reuse.
- `-NoOpen` and `NO_OPEN=1` change only opening (source ~L239 and ~L769).
- In PS, the final `Read-Host` (~L1595) is inside the same `try` as the download and
  hand-off.
- In Bash, an empty explicit `SALAH_WIDGET_PRESET_URL` disables preset staging
  (`${VAR-default}`, ~L24). PowerShell treats an empty variable as unset and uses the
  default URL (~L23).

**Hypotheses.**
- In a non-interactive PowerShell host, the hand-off `Read-Host` throws. The `catch` then
  prints a GitHub fallback warning and opens the store page after the asset was already
  handed off, and the next `Read-Host` ends the run. Traced in source; not executed.

**Unknowns.**
- Whether any test covers PS acknowledgement failure after a hand-off. None was found in
  the cited suites.

**Hardening status.**
- Hand-off re-admission, `NoOpen` semantics and truthful pending wording:
  `enforced and covered by tests` (routes8 run 43171927350; normal18 run 43171927589;
  full20 normal2 run 43220592915).
- Exit-status parity and the non-interactive acknowledgement path: `unresolved`
  (divergence; see Open findings).

---

## Open findings

Classification: (a) material acceptance blocker requiring correction; (b) documented and
verified, no change needed; (c) material, but implementation or verification incomplete;
(d) non-blocking, or out of scope for later work.

**(a) Blockers.** None.

**(b) Documented and verified, no change needed.**

| Finding | Entry |
|---|---|
| Preview guards and the whole-entry early return on both hosts, within R0016's recorded scope | 001 |
| Eligibility gating before staging and at dispatch | 002 |
| B1/B2 staging-parent rules; re-run on the merged bytes except the macOS native staging suite | 003 |
| Identity-checked scratch cleanup, and retained bundles through exit, failure, INT and TERM | 004 |
| Windows artifact admission and publication with readback | 006 |
| Transaction contract's final-parent owner rule, now corrected | 003 |

**(c) Material, but implementation or verification incomplete.**

| Finding | Entry |
|---|---|
| Host-wide zero effects and transport absence in preview are not established: no hard containment, null telemetry, and host start-up effects outside the installer's statements | 001 |
| Session-persistent `StageNative` reuse under `irm \| iex` (possibly stale predicates) | 005 |
| `posix (macos-15, Darwin)` not acquired in run 43239081990, so Apple native staging, lifetime and admission were not re-run on the merged bytes | 003, 004, 006 |

**(d) Non-blocking, or out of scope for later work.**

| Finding | Entry |
|---|---|
| PowerShell drops malformed or unknown selection tokens instead of refusing them (Bash refuses) | 002 |
| No mutant pins the private-child owner term; the refusal text under-describes the admitted owner set (recorded NOT DONE in R0015) | 003 |
| Newline check only on the supplied spelling (recorded as theoretical in R0015) | 003 |
| Kill-time or closed-console scratch leakage, and the interrupt window before a root is recorded (no prior NOT DONE record found) | 004 |
| Bash preset rewrite replaces `local=1` across the whole text, does not validate `SALAH_WIDGET_HASH` and normalises line endings; outside the Windows transaction contract | 006 |
| Bash publishes with a rename after validating the partial, without a post-rename readback. Same inode in the private root; issue 21 row 21-07 requires validation before publication | 006 |
| Transport timeouts and redirect policy (recorded NOT DONE in R0015) | 006 |
| PS non-interactive acknowledgement can trigger a store fallback after a hand-off; PS exits 0 when nothing was staged (Bash exits 1); empty preset URL differs between hosts | 007 |
| README sentence "Preview creates, overwrites and deletes no files or directories" is stronger than the host-level evidence. It was not changed, because `tools/qualification/installer_preview_docs.cjs` pins the README SHA256 and that exact phrase | 001 |

### Final focused sweep (2026-11-12, merged main `e4dbf91b`)

The merged `install.sh` and `install.ps1` were re-read for five transition classes.

1. A refused, held or unknown target reaching staging or download. Not found. Staging
   needs at least one eligible selected target (Bash ~L910–911; PS ~L1695–1700). Each
   dispatch re-derives eligibility and skips held and refused targets before any
   install or preset call (Bash ~L922–931; PS ~L1707–1719).
2. Cleanup acting on a path whose identity was not verified. Not found.
   - Bash `cleanup_staging` deletes only after `verify_root` matches the recorded
     identity (~L210). Bash does not identity-check descendants, but `rm -rf` follows no
     links inside the 0700 root.
   - PS `Clear-OwnedScratch` (~L733–740) and `Clear-StagingCompilerContext` (~L234–252)
     verify the root and every descendant first.
3. A preview path reaching staging, network, clipboard or open. Not found. Both
   installers exit at the preview branch (Bash ~L871; PS ~L1666) before terminal
   acquisition or staging, and every effectful helper is guarded.
4. An artifact used before its admission completed. Not found.
   - Bash consumers receive a path only after validation and rename.
   - PS hand-off re-checks with `Get-AdmittedArtifact` (~L1509, ~L1560, ~L1564).
5. Publication without readback. Not found against an accepted guarantee.
   - PS `Publish-OwnedFile` reads back both the copy and the published file (~L1209,
     ~L1213).
   - Bash validates the partial and renames it without a post-rename readback, which
     is classified (d) above.

No transition was traced end to end that violates an accepted staging, ownership,
transactional-publication or preview no-effect guarantee on the merged bytes.
