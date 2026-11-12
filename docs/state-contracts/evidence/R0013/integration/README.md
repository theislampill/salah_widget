# R0013 integration onto accepted main

This folder holds the integration receipts for R0013 (issue #19). It is not a
completion certificate. It does not approve a merge and does not close the issue.

## What was merged

| Item | Value |
|---|---|
| Accepted main (first parent) | `546d88281c4bdd0ae0a54d0b6ec5f9e5310c7c3a` (merge of PR #82) |
| R0013 head (second parent) | `8013b4404b55f21b43b7e62456fd24e15881b7fd` (PR #75 head, `pro/r0013-explicit-discovery-knowledge-20261106`) |
| Merge commit | `ca2099ef8c5512e7cbfbd73f0d0729459a857702`, tree `9869033530517d93366e905b88c27cb528efbcd5` |
| Method | ordinary `git merge --no-ff`. No rebase or squash. The `pro/...` branches are untouched, so the stacked R0015 and R0016 ancestry stays valid |
| Merge-base | `da12688033c9481a3fea12e6aeed68b23a385694` |
| Conflicts | none |
| Diff vs main | 275 files, +50,641/-145. 255 of them are under `evidence/R0013/`; 20 are non-evidence files |

The only file whose bytes differ from both parents is `README.md`. Its merged blob
is `30cd9c14c7ba889355714f8298ce47458c02c8aa` (sha256
`2fc5ceb2f818ab79d2f2c6e16348bcb591e5fff8252835f5954c67a6291f0eed`). Main's
R0026/R000D paragraphs and R0013's installer paragraphs auto-merged.

## What carries over by byte identity

Natively qualified source: commit `f2161ed6a1fe2e0647ee541487ab1ac792d4d3df`,
tree `77932af5`, run 42981543351.

| Path | Blob at merge | Same as f2161ed6 |
|---|---|---|
| `install.sh` | `d7f8267d2b426da79d8875f9599eeeed2696ffc8` | yes |
| `install.ps1` | `1764c72d41178b405d955c442d4411f563f5da0e` | yes |

`git diff f2161ed6 <merge>` is empty over these paths: `install.sh`,
`install.ps1`, `tests/install*`, `tools/qualification/installer_native.py` and
`.github/workflows/installer-native.yml`.

All 18 `sourceBindings` in
`native-attempt-4/review-bindings-and-complete-denominator.json` have the same git
blob at the merge commit. That includes the workflow blob `3815d6ad`.

What changed under the installer suites is indirect. `tests/install-builder.cjs`
reads `src/native/builder.html` and `src/native/config.js`, and both come from main:

| File | Merged sha256 | R0013 head sha256 |
|---|---|---|
| builder | `873e8ded…` | `66f1cd86…` |
| config | `719efed9…` | `91a37863…` |

That is why criterion 19-08 must be re-established at the integration tree.

## Integration-owned additions

- `.github/workflows/r0013-integration-qualification.yml`. This is a copy of the
  `installer-native.yml` jobs with `--phase r0013` fixed. It runs on push to
  `claude/r0013-integration-*` and on `workflow_dispatch`, and its path filter is
  the original set plus the new file itself. Its header comment lists every
  difference from the original. The original workflow is untouched.
- This folder.
- The "Integration onto main" section of `docs/state-contracts/R0013.md`.

## What was re-run, and where

Local runs on the integration tree (Windows 11 host; not a substitute for the
hosted cells):

| Suite | main 546d8828 | integration |
|---|---|---|
| `node --test tests/*.test.cjs tests/*.test.mjs` | 959 / 955 pass / 0 fail / 4 todo | 959 / 955 / 0 / 4 |
| `node --test tests/real-sky/*.test.mjs` | 354 | 354 / 354 |
| `node --test moon/tests/*.test.cjs` | 133 | 133 / 133 |
| `node tests/rlgwo-docs-contract.cjs` | exit 1, 50/64 | exit 1, 50/64. The per-case status map is identical; 0 cases changed |
| `python tools/build_native.py` twice | — | exit 0 twice; tree clean |
| `python tools/verify_v1.py` | — | PASS |
| `tests/install-builder.cjs`, default env | — | exit 1, 3/4 |
| same with `SALAH_TEST_BASH` = Git Bash | — | exit 0, 4/4 |
| `installer_native.py --phase r0013`, WSL Ubuntu (Bash 5.2.21) | — | PASS. Collector exit 0. 26/26, 25/25, 76/76, 10/10, 13/13, 8/8, 4/4 |

The default-env `install-builder` failure is an environment issue on Win32. Node
spawns `/bin/bash`, which resolves to a path that does not exist, so `status` is
`null`. The hosted Windows job never runs this suite.

Local PowerShell results are recorded in the R0013.md integration section. Two
limits apply:

- Local PS7 is 7.6.9, not the pinned 7.6.6, so the collector's version gate stops
  locally by design.
- The PS5.1 root-array-only mutant survives, as it did before. It gets no credit.

## Hosted run 43120878720

Receipts are in `hosted-43120878720/`. They include the three artifact tarballs as
downloaded, each OS's `result.json`, the two failing Windows receipts and
`summary.json`.

The run was a push of head `302c4ec0a340fd2c07789598838f35acf5652194` (tree
`9169e944`). Its overall conclusion is **failure**.

| Job | Conclusion | Suites |
|---|---|---|
| posix (ubuntu-24.04, Linux), Bash 5.2.21 | success | install-bash 26/26, entry-bash 25/25, discovery 76/76, detectors 10/10, discovery-mutations 13/13, original-mutations 8/8, **install-builder 4/4** |
| posix (macos-15, Darwin), Apple Bash 3.2.57 | success | 26/26, 25/25, 76/76, detectors 12/12, 13/13, 8/8, **install-builder 4/4** |
| windows (PS 5.1.20348.5773 + 7.6.6) | **failure** | 9 PASS, 2 FAIL. The rows follow |

Windows rows:

- PS5.1: components 18/18, guards 10/10, discovery 78/78. Mutations: paired
  control plus 13 mutants detected; the root-array-only mutant gets no credit.
- PS7: bootstrap 4/4, components 18/18, guards 10/10, discovery 78/78.
  Mutations: paired control plus 14 mutants detected.
- **`ps51-install-host-bootstrap` FAIL (exit 0), 0/4.** This is the same retained
  failure as reference run 42981543351. It is the no-installer PS5.1 startup
  diagnostic: `BOOTSTRAP_BLOCKED_TIMEOUT` after phase `join-path-begin`, with
  `installerExecuted=false`.
- **`install-entry-native` FAIL (exit 1).**
  - PS7: 12/12 PASS.
  - PS5.1 case `github`: FAIL. The literal error is "timed out after 25 seconds",
    classified `BOOTSTRAP_BLOCKED`.
  - The host never loaded the interception module and reached no installer
    phase. The snapshot was unchanged and there were no effects.
  - The driver stops after a blocked host bootstrap (`break`, by design), so the
    other 11 PS5.1 entry cases were not acquired in this run.
  - The reference run passed this suite 24/24.

Diagnosis:

- **Not a workflow-copy defect.** The step is identical apart from the literal
  `--phase r0013`.
- **Not a regression against main's builder or config.** `install-builder` passes
  4/4 on both POSIX hosts. `install.ps1` and the entry tests are byte-identical to
  `f2161ed6`, and this suite reads neither builder nor config.
- **Most likely cause: hosted PS5.1 host-startup timing**, the same
  `BOOTSTRAP_BLOCKED` class as the retained diagnostic. A Windows entry timeout of
  the same kind was also recorded in `native-attempt-2` on the same runner image
  `20261101.353.1`.
- This is a diagnosis, not a PASS. Attempt 1 did **not** re-acquire the PS5.1
  full-file entries at the integration tree.

### Attempt 2 (`gh run rerun --failed`, same head, Windows job only)

Receipts are in `hosted-43120878720/attempt-2/Windows/`; the attempt-1 receipts
are kept unchanged. The conclusion is still **failure**.

- **`install-entry-native` PASS, 24/24** (12 per host). This acquires the PS5.1
  full-file entries at the integration tree.
- **`ps51-install-host-bootstrap` FAIL, 0/4.** All four variants hit the 15 s
  timeout after `join-path-begin`.
- Every other row passes with the same counts as attempt 1.

PS5.1 entry wall times, from fixture file times:

| Case | Seconds |
|---|---|
| `github` (first case; cap 25 s) | 23.2 |
| the other ten cases | 18.7–19.4 |
| `bad-option` | 0.2 |

The 25 s entry cap is therefore marginal on this hosted host. Run 42981543351
measured 23.0 s and 19.8–20.3 s for the same cases.
