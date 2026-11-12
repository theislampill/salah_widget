> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane F: audit baseline inventory

Baseline: main `363c3e536c8004935ef80230e43f7712e339e3a5`, tree `647b7159a60ceb7dc650563890a5a5a63af14319`. Historical reference: `f71fef6ccf7e4efcb57b5a26688d2360461a3253`. All facts were read on 2026-11-12 with `git` in the audit worktree and with read-only `gh` calls.

## 1. Public deployment identity

| Fact | Value | Source |
|---|---|---|
| Pages build type | `legacy`, branch `main`, path `/`, https enforced | `gh api repos/.../pages` |
| Latest Pages build | commit `363c3e536c8004935ef80230e43f7712e339e3a5`, status `built`, created 2026-11-12T15:41:19Z, duration 175.9 s, error null | `gh api repos/.../pages/builds/latest` |
| Deploying workflow | `pages build and deployment` (`dynamic/pages/pages-build-deployment`). It is not a file in the tree. Every merge to main from `eebba178` through `363c3e53` has a successful run. `294d2d37` has two `startup_failure` runs and then a success | `gh api .../actions/runs?branch=main` |
| Public byte readback (this audit) | `index.html` `e3a3dedb…`, `offline.html` `0c89c2e2…`, `install.sh` `27442c0e…` and `install.ps1` `07671cb9…` served by github.io equal the baseline tree. `raw.githubusercontent.com/.../main/install.sh` also equals `27442c0e…` | `curl` and `sha256sum` |
| Pages exclusion | `_config.yml` excludes only `docs/rlgwo-execution/20261014/R000C/native` (7,266 files, 300.7 MB). A sample excluded path returned 503. A sample 53 MB evidence ZIP under `docs/real-sky/evidence/...` is served (HTTP 200) | `curl -I` |
| Estimated publishable payload | 0.898 GB at PR62 (`06772824`), 1.771 GB at `f71fef6c`, 1.910 GB at baseline (9,686 files) | Sum of git blob sizes, minus the `_config.yml` exclusion and dot/underscore paths. This is an estimate, not a `_site` measurement |

## 2. RLGWO work-order inventory (39 issues, all `CLOSED` / `COMPLETED`)

Certificate column: **FINAL** means a comment carrying a `<!-- Rxxxx-FINAL-CERTIFICATE:<sha>:<date> -->` marker (comment id shown, with the bound sha). **Closure** means an earlier-style closure comment (id shown) and no FINAL marker. The `gh ... select(test("CERTIFICATE|certificate"))` query also matches the 2026-10-09 "remaining-work specification" comments, so the matches were classified by marker.

| RLGWO | Issue | Closed (UTC) | Certificate / closure comment | Main merge(s) that carried it (first-parent) | State contract |
|---|---|---|---|---|---|
| R0001 | 1 | 2026-10-09 | Closure 6073040128 ("RLGWO closure proof") | #42 `18ff1486` (evidence commit `9cd9dfa3` is on side branch `codex/rlgwo-closure-audit-20261008`, not on main) | none |
| R0002 | 2 | 2026-10-14 | Closure 6163956116 (`CLOSE-R0002:daaada05`) | #57 `daaada05` | none |
| R0003 | 3 | 2026-11-11 | FINAL 6805636415 (`a4766a1b`); earlier CLOSE 6182373378 | #79 `a4766a1b` | R0003.md |
| R0004 | 4 | 2026-10-14 | Closure 6165919700 | #58 `c431733c` | none |
| R0005 | 5 | 2026-10-09 | Closure 6073058182 | #42 `18ff1486` | none |
| R0006 | 6 | 2026-10-14 | Closure 6168140633 | #59 `7827099d` (docs #51 `ec6e6282`, a direct first-parent commit) | none |
| R0007 | 7 | 2026-11-11 | FINAL 6787290418 (`dbf3370f`); earlier CLOSE 6162239043 | #56 `9d1bffe0`, #73 `dbf3370f` | R0007.md |
| R0008 | 8 | 2026-10-12 | Closure 6125639418 (`qualified-delivery:419301cb`, side branch) | Cites #46 `80e70386` and #48 `ec76c7e3`. Exact code carrier not determined | none |
| R0009 | 9 | 2026-10-09 | Closure 6073043445 | #42 `18ff1486` | none |
| R000A | 10 | 2026-10-09 | Closure 6073045468 | #42 `18ff1486` | none |
| R000B | 11 | 2026-11-11 | FINAL 6788969371 (`da126880`); CLOSE 6178041776 / 6178186713 / 6178296345 | #61 `763a460e`, #72 `da126880` (docs #53 `4e786ff5`) | R000B.md (+ ACCEPTANCE / CONTINUE / IMPLEMENTATION_PLAN / INTEGRATION) |
| R000C | 12 | 2026-10-14 | Closure 6172238574 | #60 `16658749` | none |
| R000D | 13 | 2026-11-11 | FINAL 6791942315 (`645b53cc`) + post-closure correction 6792330574; earlier CLOSE 6183596140 | #63 `ed5e7afb`, #74 `645b53cc` | R000D.md |
| R000E | 14 | 2026-10-09 | Closure 6073043480 | #42 `18ff1486` | none |
| R000F | 15 | 2026-11-11 | FINAL 6806041365 (`32f97b06`) | #80 `32f97b06` | R000F.md |
| R0010 | 16 | 2026-10-12 | Closure 6121872901 | #44 `88926dd1` | none |
| R0011 | 17 | 2026-10-12 | Closure 6132405695 (cites side commits `ac902173`, `b24ffa72`) | #50 `15367794`, #52 `83f3a86f` | none |
| R0012 | 18 | 2026-10-09 | Closure 6073058047 | #42 `18ff1486` | none |
| R0013 | 19 | 2026-11-12 | FINAL 6814244464 (`a1072ae1`) | #84 `a1072ae1` (#75 `ca2099ef` merged into a work-order branch; reached main through #84) | R0013.md |
| R0014 | 20 | 2026-10-12 | Closure 6126260975 (PR48 delivery; cites side commits `3bed0f01`, `de508730`) | #48 `ec76c7e3` (docs) | none |
| R0015 | 21 | 2026-11-12 | FINAL 6828391831 (`363c3e53`); post-merge evidence 6816287579; reopened after an unintended auto-closure (6816192574) | #85 `3b0e6141` (+ docs #87 `363c3e53`) | R0015.md + `docs/r0015-artifact-transactions.md` |
| R0016 | 22 | 2026-11-12 | FINAL 6828374683 (`e4dbf91b`) | #86 `e4dbf91b` | R0016.md |
| R0017 | 23 | 2026-11-11 | FINAL 6785616297 (`539c1366`); earlier CLOSE 6181111816 / 6181220586; WITHDRAWN 6703510170 | #54 `00d8d446` (direct), #62 `06772824`, #70 `eebba178`, #71 `539c1366` | R0017.md |
| R0018 | 24 | 2026-10-15 | Closure 6191194425 | #64 `ae24fec4` | none |
| R0019 | 25 | 2026-10-13 | Closure 6143489619 | #55 `3c4221c5` | none |
| R001A | 26 | 2026-10-09 | Closure 6073051392 | #42 `18ff1486` | none |
| R001B | 27 | 2026-10-12 | Closure 6127444270 | #49 `b690bc35` | none |
| R001C | 28 | 2026-10-12 | Closure 6124639912 | #45 `0e3a3ad6` | none |
| R001D | 29 | 2026-10-09 | Closure 6073052323 | #42 `18ff1486` | none |
| R001E | 30 | 2026-10-09 | Closure 6073045350 | #42 `18ff1486` | none |
| R001F | 31 | 2026-10-09 | Closure 6073059811 | #42 `18ff1486` | none |
| R0020 | 32 | 2026-10-12 | Closure 6124693557 (`RLGWO-CLOSE:R0020`) | #46 `80e70386` | none |
| R0021 | 33 | 2026-11-11 | FINAL 6809435795 (`5279958a`); CLOSE-R0021 6326407465 (`f71fef6c`) | #67 `f71fef6c`, #81 `294d2d37`, #83 `5279958a` | R0021.md |
| R0022 | 34 | 2026-10-16 | Closure 6220885146 | #66 `f270792f` | none |
| R0023 | 35 | 2026-10-12 | Closure 6125047409 | #47 `ba6d15d6` | none |
| R0024 | 36 | 2026-10-15 | Closure 6201665819 | #65 `fc8d1333` | none |
| R0025 | 37 | 2026-10-14 | Closure 6157899631 (cites side commit `9a6124df`) | #42 `18ff1486` cited. Exact carrier not determined | none |
| R0026 | 68 | 2026-11-11 | FINAL 6804824819 (`7f2e8d16`) | #78 `7f2e8d16` (#76 was closed unmerged) | R0026.md |
| R0027 | 69 | 2026-11-12 | FINAL 6810490146 (`546d8828`) | #82 `546d8828` | R0027.md |

Summary:
- 39 of 39 issues are closed (completed). 12 carry a FINAL-CERTIFICATE marker: R0003, R0007, R000B, R000D, R000F, R0013, R0015, R0016, R0017, R0021, R0026 and R0027. Exactly these 12 have a `docs/state-contracts/` contract.
- The other 27 carry a closure comment of an older style. Ten of them closed on 2026-10-09 against PR #42 with evidence on side branches.
- Main has 39 first-parent merges plus direct commits #51–#54.
- PRs #38 (37-work-order integration), #43 and #77 remain OPEN.
- The FINAL markers on R0015 and R0016 carry the date "2026-11-13". The comments were created 2026-11-12T15:48Z.

## 3. Repository tree classification at baseline (16,996 files, 2.211 GB)

Rules: probe `probes/F/classify.py`. "Generated" means outputs written by `tools/build_native.py` and `tools/build_moon.py`. The root `config.js` and `builder.html` are copies of `src/native/*`.

| Class | Files | Bytes | Share | At `f71fef6c` |
|---|---|---|---|---|
| Retained historical evidence (`docs/rlgwo-execution`, `docs/state-contracts/evidence`, `docs/real-sky/evidence`, `docs/moon/evidence`, archives, `plans/`) | 16,119 | 1,878.8 MB | 85.0 % | 13,454 / 1,745.3 MB |
| Generated output (root entries, `real-sky/core/**`, real-sky bundles and CSS, notices, Moon host, worker and chunks, BUILD) | 117 | 165.4 MB | 7.5 % | 117 / 165.3 MB |
| Vendored or data (`vendor/**`, `moon/assets/**`, WASM, Moon manifests, `presets/`, `real-sky/checkpoint.json`) | 195 | 157.0 MB | 7.1 % | 195 / 157.0 MB |
| Tests (`tests/**`, `moon/tests/**`) | 280 | 4.06 MB | 0.18 % | 189 / 2.04 MB |
| Tooling (`tools/**`, `.github/**`) | 185 | 2.65 MB | 0.12 % | 91 / 0.79 MB |
| Authored source and docs (`src/native/*`, `real-sky/native-*`, `moon/src/*`, installers, root `*.md`, state-contract `*.md`) | 95 | 2.44 MB | 0.11 % | 71 / 1.43 MB |
| Frozen v1 (`v1/**`) | 5 | 0.29 MB | 0.01 % | 5 / 0.29 MB |

Evidence-volume facts. These are reported as facts, not as judgements.

| Location | Files | Bytes |
|---|---|---|
| `docs/real-sky/evidence` | 1,468 | 952.6 MB |
| `docs/rlgwo-execution` | 11,504 | 748.2 MB (unchanged since `f71fef6c`) |
| `docs/state-contracts/evidence` | 2,661 | 133.5 MB (all added after `f71fef6c`) |
| `docs/moon/evidence` | 435 | 40.9 MB |

`docs/state-contracts/evidence` by work order:

| Work order | Files | Bytes |
|---|---|---|
| R0021 | 541 | 42.5 MB |
| R000F | 90 | 20.2 MB |
| R0003 | 114 | 14.0 MB |
| R0026 | 92 | 12.7 MB |
| R0007 | 329 | 8.9 MB |
| R0015 | 181 | 8.3 MB |
| R0016 | 277 | 7.3 MB |
| R0013 | 303 | 5.8 MB |
| R000B | 409 | 4.6 MB |
| R0017 | 256 | 3.6 MB |
| R0027 | 37 | 3.0 MB |
| R000D | 32 | 2.7 MB |

Change from `f71fef6c` to `363c3e53`:
- `git diff --stat`: 2,935 files changed, 605,607 insertions.
- Workflows: 1 → 32 (36 registered in Actions, three of them no longer in the tree).
- `tests/`: 178 → 268 files.
- `tools/qualification`: 0 → 48 files.
- `tools/qa`: 15 → 27 files.
- Installers: `install.sh` 767 → 952 lines, `install.ps1` 614 → 1,741 lines.
