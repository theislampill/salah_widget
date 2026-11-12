# R0015 integration, stacked on the R0013 integration

This folder holds the integration receipts for R0015 (issue #21). It is not a
completion certificate. It does not approve a merge and does not close the issue.

## What was merged

| Item | Value |
|---|---|
| First parent | `4d46794c9793b85ab8f6e70c6b993e65be67f4f0`, the R0013 integration head (tree `9eca3a3d`). That branch merges R0013 `8013b440` onto accepted main `546d88281c4bdd0ae0a54d0b6ec5f9e5310c7c3a` |
| Second parent | `bf566111fe530b5de2c7c63ca4586e83d5f4b965`, the PR #77 head, branch `pro/r0015-explicit-artifact-transactions-20261106` |
| Merge commit | `b19bed64248f3f06855d126bae2bb32d83ee340a`, tree `4df9c88b5efd016bbf646af266aa3135824d073a` |
| Branch | `claude/r0015-integration-20261111` |
| Method | ordinary `git merge --no-ff`. No rebase or squash. The `pro/...` branches are untouched, so R0016's ancestry stays valid |
| Conflicts | none. `README.md` auto-merged |
| Diff vs first parent | 143 files, +33,266/-148. 22 are non-evidence files |

The only file whose bytes differ from both parents is `README.md`. Its merged blob
is `db9c0ddd` (sha256 `42cfc52c…`). It contains:

- R0015's review-first pin lines, unchanged: `d96f87825f02077da7f6afe742d30aecfd1fc005`
  and `$InstallCommit`;
- R0015's retained-bundle lifetime text;
- main's R0026/R000D paragraphs.

## What carries over by byte identity

The native qualification run is 43028305607 at `d96f8782`, tree `5911c099`.
Between `d96f8782` and `bf566111`, the non-evidence changes are only
`README.md`, `docs/r0015-artifact-transactions.md`, `docs/state-contracts/R0013.md`
and `R0015.md`.

`git diff d96f8782 <merge>` is empty over all of these:

- `install.sh` and `install.ps1`
- `tests/install*` and `presets/`
- `tools/qualification/installer_native.py` and `windows_installer_probe.{ps1,py}`
- `.github/workflows/installer-native.yml` (blob `456f88c8`) and
  `installer-diagnostic.yml` (blob `789197ca`)

Installer blobs at the merge:

| Path | Blob | Same as |
|---|---|---|
| `install.sh` | `d7f8267d` (sha256 `609ecb0b…`) | R0013 |
| `install.ps1` | `f2ee2fff` (sha256 `ab2d8470…`) | R0015 |

As in R0013, `tests/install-builder.cjs` reads main's `src/native/builder.html` and
`config.js`, so the run is repeated on the integrated tree.

## Integration-owned additions

`.github/workflows/r0015-integration-qualification.yml`:

- **Triggers:** push to `claude/r0015-integration-*`, and `workflow_dispatch`.
- **Path filter:** the original set plus the new file itself, so a docs- or
  evidence-only push does not run it.
- **Jobs `posix` and `windows`:** a structural copy of R0015's
  `installer-native.yml` jobs with `--phase r0015` fixed.
- **Job `windows-r0013-phase`:** an extra copy of the `windows` job with
  `--phase r0013`. With R0015's collector, phase r0015 runs only the
  positive/no-open entries. Phase r0013 runs R0013's full twelve-scenario entry
  set and the bootstrap diagnostic under R0015's 60 s instruments. That is how
  R0013's Windows rows (ES13-13) are evaluated on the stacked tree.

`installer-native.yml`, `installer-diagnostic.yml` and
`r0013-integration-qualification.yml` are unchanged.

## Local runs (Windows 11 host; not a substitute for hosted cells)

| Suite | Result on the integrated tree |
|---|---|
| `node --test tests/*.test.cjs tests/*.test.mjs` | 959 / 955 / 0 fail / 4 todo (same as main) |
| `tests/real-sky` | 354 / 354 |
| `moon/tests` | 133 / 133 |
| `rlgwo-docs-contract.cjs` | exit 1, 50/64. Per-case map identical to main; 0 cases changed |
| `build_native.py` twice | exit 0 both times; tree clean |
| `verify_v1.py` | PASS |
| WSL Ubuntu Bash 5.2.21, `installer_native.py --phase r0015` | 8 of 9 PASS: install-bash, entry-bash, discovery, detectors, discovery-mutations, original-mutations, builder, staging-native |

The ninth WSL command, `install-linux-owner`, exits 2. Its foreign-owner rows are
`BLOCKED`, with the reason "No privileged supervisor with mapped distinct subject
UID/GID". This host has no passwordless sudo, which the test requires. Its local
same-UID positive passes. This is environmental: the hosted ubuntu-24.04 runner
supplies the supervisor.

The local PowerShell collector was run in a disposable scratch copy whose PS7
version gate was relaxed to accept 7.6.9. Hosts were PS 5.1.26100 and PS 7.6.9.

- **Non-transaction suites pass:** components, guards, discovery and discovery
  mutations on both hosts. The bootstrap probe is `ACQUIRED` on both.
- **Transaction, staging, compiler, volume and long-path suites fail.** So do the
  entry cases.
  - The installer refuses with "Compiler ancestor permits foreign replacement or
    has an untrusted owner", or the fixture reports "Owned parent ACL setup
    failed".
  - On this development host, the user `%TEMP%` carries write access for a local
    sandbox tooling group and several foreign SIDs.
  - R0015's fail-closed ancestry check is designed to refuse exactly that.
- This is an environment property of the host, not product evidence either
  way. The hosted cells below are the qualification.

## Hosted run 43127269742 (attempt 1)

Receipts are in `hosted-43127269742/`: four artifact tarballs, `result.json` per
job, the Windows bootstrap and entry receipts, and `summary.json`.

The run was a push of head `6c1b7c0f9adb74179da0fcbd0cfe40a243702e83` (tree
`56386fbb`). Its conclusion is **success**, with all four jobs successful.

| Job | Result |
|---|---|
| Linux, Bash 5.2.21, phase r0015 | PASS. 9/9 commands: install-bash 26, entry-bash 25, discovery 76, detectors 10, discovery-mutations 13, original-mutations 8, builder 4, staging-native 9, linux-owner 3 |
| Darwin, Apple Bash 3.2.57, phase r0015 | PASS. 8/8 commands, same counts, detectors 12 |
| windows, phase r0015 | `OBSERVATIONS_ACQUIRED`; qualification `PASS`; diagnostics `COMPLETE`. 22/22 qualification commands pass, including transactions 28/28, staging 8/8, compiler custody 12/12, volume policy 13/13, volume mutations 2/2, transaction mutations 22/22 per host, PS7 long-path refusal 1/1, and entry-native 4/4 (positive/no-open). Diagnostics (bootstrap and first-call, both hosts) are `ACQUIRED` |
| windows-r0013-phase, phase r0013 | `OBSERVATIONS_ACQUIRED`; qualification `PASS`; diagnostics `COMPLETE`. PS5.1/PS7 components 18, guards 10, discovery 78, mutations control+13 / control+14. **entry-native 24/24.** Bootstrap probe `ACQUIRED` on both hosts |

PS5.1 timings from the receipts:

- Bootstrap: every cold and warm probe reached `script-completed`. The
  `join-path` interval was 11.2–16.4 s in the `windows` job and 22.7–27.6 s in
  the `windows-r0013-phase` job.
- Entry wall time in the r0013-phase job: 23.5–26.0 s. `positive` took 26.0 s
  and `no-open` 25.1 s, both above R0013's original 25 s cap. `bad-option` took
  0.3 s.

Both measurements confirm that R0013's 15 s and 25 s caps were below this hosted
host's PS5.1 first-command cost. Under R0015's 60 s instruments, everything
completes.
