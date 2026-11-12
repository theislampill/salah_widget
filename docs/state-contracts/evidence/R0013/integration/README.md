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

The README PowerShell review-first pin was later re-pinned from `f2161ed6` to
`8dfe944f` (`install.ps1` `cf353a7f`). The Bash pin stays at `f2161ed6`
(`install.sh` `d7f8267d`, unchanged). The re-pin makes `README.md` the only
path that conflicts in `git merge-tree` against R0015 `bf566111`. That
documentation-only conflict is expected and is resolved in the R0015
integration merge. The paragraph below describes the first merge.

The only file whose bytes differ from both parents is `README.md`. Its merged blob
is `30cd9c14c7ba889355714f8298ce47458c02c8aa` (sha256
`2fc5ceb2f818ab79d2f2c6e16348bcb591e5fff8252835f5954c67a6291f0eed`). Main's
R0026/R000D paragraphs and R0013's installer paragraphs auto-merged.

## Byte identity at the first merge (history)

At merge commit `ca2099ef` the installer bytes equalled the natively qualified
source `f2161ed6a1fe2e0647ee541487ab1ac792d4d3df` (tree `77932af5`, run
42981543351): `install.sh` `d7f8267d`, `install.ps1` `1764c72d`, and
`git diff f2161ed6 ca2099ef` was empty over `install.sh`, `install.ps1`,
`tests/install*`, `tools/qualification/installer_native.py` and
`.github/workflows/installer-native.yml`. All 18 `sourceBindings` in
`native-attempt-4/review-bindings-and-complete-denominator.json` had the same
blob at that commit. **This is no longer the state of the candidate;** see the
next section.

## Current candidate: what differs from f2161ed6

| Path | Candidate blob | Same as f2161ed6 |
|---|---|---|
| `install.sh` | `d7f8267d2b426da79d8875f9599eeeed2696ffc8` (sha256 `609ecb0b…`) | yes |
| `install.ps1` | `cf353a7fee6163564f898e9cbe666bad70d787b7` (sha256 `ba6c4561…`) | **no** (was `1764c72d`) |

`git diff --stat f2161ed6 <candidate>` over the installer paths above lists
exactly seven files: `install.ps1`, `tests/install-discovery.ps1`,
`tests/install-discovery-mutations.py`, the new `tests/install-json-lexer.ps1`,
`tests/install-json-lexer-repro.ps1` and `tests/install-json-lexer-mutations.py`
(all six from the lexer merge below), and `tests/install-host-bootstrap.ps1`
(adopted from R0015, below). `tools/qualification/installer_native.py` and
`installer-native.yml` are unchanged. Because `install.ps1` changed, the
review `sourceBindings` that name `install.ps1` no longer match the candidate.

### Merged lexer correction 8dfe944f

The installer executor's corrective commit
`8dfe944f843548603df260b78ccd1df4aa228a8e` (child of `8013b440`, branch
`pro/r0013-json-lexer-fix-20261112`) was merged with `--no-ff` as `a3783f2a`,
without conflicts. In `Test-StrictJson` it replaces the per-token
`$lexer.Match($Json,$position)` restart (quadratic on large metadata) with one
continued match sequence (`Match` / `NextMatch`), keeps the contiguous-index
check, and additionally requires `$position -eq $Json.Length` at the end. The
token grammar, parser states and duplicate-key handling are unchanged. It also
adds a literal bracketed-profile discovery case (79 discovery cases) and a
`wildcard-profile-probe` discovery mutant, plus the lexer equivalence /
performance suite, reproducer and lexer mutation controls.

The independent review of this correction reported 4000/4000 differential
agreement between the old and new validators on PS5.1 and PS7.6.9, linear
timing, and that the old validator fails the performance test on PS7. Those
review numbers are relayed here; this integration did not re-observe the 4000-
case differential. The performance budget is 30 s per sample on native PS5.1
(the executor's disclosed choice from its original near-linear PS5.1
measurements) and 5 s elsewhere, with both median doubling ratios required
to be ≤ 3×.

### Bootstrap harness taken from R0015

`tests/install-host-bootstrap.ps1` is taken byte-identically from R0015 commit
`bf566111` (blob `dcde45db3967f6e658735d10c06a71e8f20f4d5f`) as commit
`6bc3007c`. It never executes the installer. Its original premise, that a
private-cache PS5.1 child reaches its first cmdlet within 15 s on the hosted
image, is invalid there: hosted R0015-harness readiness for PS5.1 children
was 11.7–34.0 s (receipts below). The adopted version uses a bounded 60 s
child budget, timestamps phases and records cold and warm children. Its
default variant set is two of the original four (`native-only` and
`private-wildcard-cmdlets`, each cold and warm); the two export-diagnostic
variants (`private-explicit-cmdlets`, `private-no-cmdlets`) run only with
`-VariantSet Exports`, which no collector passes, so they are not run. They are
diagnostics, not product assertions. `tests/install-entry-native.py` was **not**
adopted from R0015: that version asserts R0015-only installer behaviour.

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
  difference from the original. The original workflow is untouched. Later
  integration commits added a `windows-json-lexer` job (PS5.1, 7.6.6, 7.6.9;
  `28fd719d`), and a `windows-2025` leg of the `windows` job next to the
  contract host `windows-2022`. They also mirrored R0015's Windows job env and
  60-minute budget (`ddfb872a`). A disclosed PS5.1 warm-up step was added in
  `ab5bc2d4` and removed in `ddfb872a` because it changed nothing.
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

## Later hosted runs (Windows receipts)

Receipts are in `hosted-43143993057/`, `hosted-43145016304/` and
`hosted-43146668695/` (including `attempt-2/` and `attempt-3/`). Each leg
folder holds `result.json`, `ps51-install-host-bootstrap.json`,
`install-entry-native.json` and, when non-empty, its stderr. Each run's
`summary.json` gives per-suite results and the sha256 of the full artifact
tarball, which is not committed. `Windows/` is the contract host
windows-2022 (image `20261101.353.1`; PS 5.1.20348.5773, PS 7.6.6).
`Windows-windows-2025/` is an extra observation leg (image `20261103.298.1`;
PS 5.1.26100.33648, PS 7.6.6). POSIX jobs passed in every run below.

| Run (head) | Leg | Bootstrap (ps51) | install-entry-native | Job |
|---|---|---|---|---|
| 43143993057 (`28fd719d`, lexer job added) | 2022 | FAIL: `native-only` timed out at 15 s after `join-path-begin`; the other three variants completed | PASS 24/24 | failure |
| 43145016304 (`ab5bc2d4`, warm-up added) | 2022 | FAIL 0/4, all at 15 s after `join-path-begin` | FAIL: ps51 `github` `BOOTSTRAP_BLOCKED` (25 s), interception never loaded; 12 ps7 cases passed | failure |
| 43145016304 | 2025 | FAIL 0/4, same | FAIL: collector 240 s timeout, no receipt | failure |
| 43146668695 attempt 1 (`ddfb872a`, R0015 harness) | 2022 | PASS 4/4 (readiness 22.8–28.1 s) | FAIL: collector 240 s timeout, no receipt | failure |
| 43146668695 attempt 1 | 2025 | PASS 4/4 (22.4–34.0 s) | FAIL: 20/21 acquired cases passed; ps51 `missing-preset` `BOOTSTRAP_BLOCKED`, interception never loaded | failure |
| 43146668695 attempt 2 (`rerun --failed`) | 2022 | PASS 4/4 (11.7–17.8 s) | **PASS 24/24** | **success**: all 11 suites PASS |
| 43146668695 attempt 2 | 2025 | PASS 4/4 (22.4–27.9 s) | FAIL: collector 240 s timeout, no receipt | failure |
| 43146668695 attempt 3 (`rerun --failed`, 2025 only) | 2025 | PASS 4/4 (22.2–27.2 s) | FAIL: collector 240 s timeout, no receipt | failure |

In every leg above, every other Windows suite passed: PS5.1 and PS7
components, guards, discovery and discovery mutations. In the same runs the
`windows-json-lexer` jobs passed on PS5.1, 7.6.6 and 7.6.9. In 43146668695
attempt 1 that was lexer 52/52, discovery 79/79, lexer mutations 3/3 plus the
redundant-Index survivor (no credit), and discovery mutations 16/16 (PS7) or
15/15 plus the PS5.1 singleton survivor (no credit). PS5.1 1 MiB median was
5.09 s against the 30 s budget, with doubling ratios 2.00 and 2.01. Those
reports are in `hosted-43146668695/json-lexer-*/`.

What this establishes, and what it does not:

- **windows-2022 is the contract host.** Its `windows` job is green in
  43146668695 attempt 2, with all 11 suites passing, including
  `install-entry-native` 24/24 at the candidate tree.
- **windows-2025 is an extra observation leg and is not green.** It failed in
  every attempt, each time only on `install-entry-native`.
- **The bootstrap diagnostic no longer fails** with the adopted R0015 harness:
  it passed on both images in all three attempts of 43146668695. It failed
  under the original 15 s harness in 42981543351, 43120878720 (attempts 1–2),
  43143993057 and 43145016304. Those failures are preserved.
- **`install-entry-native` is unmodified (25 s per-case cap) and intermittent
  on hosted Windows.** Where a receipt exists, every failing case is
  `BOOTSTRAP_BLOCKED` with interception never loaded, so no installer phase
  was reached. The four collector-timeout failures (240 s collector cap) left no
  per-case data. Their cause is inferred, not proven.
- The warm-up step in 43145016304 measured about 0.35 s for a PS5.1 first
  cmdlet in the runner's own environment on both images. It did not help the
  test's private-cache children and was removed.
