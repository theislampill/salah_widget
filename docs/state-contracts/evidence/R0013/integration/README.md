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

Hosted qualification receipts are added under `hosted-<run id>/` by a follow-up
commit, bound to the run id and head SHA they were produced on.
