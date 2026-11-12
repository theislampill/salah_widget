> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane F: installers, build and generation, deployment and qualification workflows

Baseline: `363c3e53` (tree `647b7159`). Comparison point: `f71fef6c`. Read-only audit. Probes ran only in `probes/F/` (a disposable `git archive` copy of the build inputs). The worktree's `git status --porcelain --ignored` stayed empty throughout. The baseline inventory is in `F-baseline-inventory.md`.

## 1. Machine census

### Installer registry verification (ISM-INST-001…007)

- **Baseline match.** `IMPLICIT_STATES.md` was written against main `e4dbf91b`, with blobs `install.sh` `e2e2640e` and `install.ps1` `28cfdae7`. The baseline has the same blobs (`git rev-parse HEAD:install.sh`). `git log e4dbf91b..363c3e53 -- install.sh install.ps1 README.md presets` is empty.
- **Line references.** Spot-checked anchors are exact at the baseline: `Initialize-Staging` L693, `Test-StrictJson` L942, `Get-FirefoxExtensionStatus` L1014, `Download-Asset` L1334, `Expand-ChromiumAsset` L1371, `Download-Preset` L1467, `firefox_status` L361, `download_preset` L701.
- **Result.** All seven entries still describe the baseline bytes. They are not redone here.

### C08: Installer discovery, selection, dry preview and manual hand-off

- **Maps to.** ISM-INST-001 (run mode and preview boundary), ISM-INST-002 (discovery and eligibility), ISM-INST-007 (hand-off).
- **Disposition.** `resolved and independently verified` within the recorded scopes.
- **Changed by.** R0013 (#19, PR #84 `a1072ae1`) made discovery knowledge explicit. R0016 (#22, PR #86 `e4dbf91b`) made preview offline.
- **Enforcement.** `discovery_eligibility` (install.sh L470) and `Get-DiscoveryEligibility` (install.ps1 L1091) are re-derived at preview, before staging and at dispatch.
- **Verification.**
  - Tests: `tests/install-discovery.py`, `tests/install-discovery.ps1`, `tests/install-discovery-mutations.py`.
  - Native runs: 42978215112 (macOS Bash 3.2.57) and 43146668695 (windows-2022 green on attempt 2; windows-2025 failed in all attempts, per ISM-INST-002); R0016 runs 43173749688/709, 43171927589/350 and 43220592915.
  - Certificates 6814244464 (R0013) and 6828374683 (R0016).
- **Residuals.** These are already in the registry:
  - PowerShell drops malformed selection tokens silently.
  - The PowerShell Chromium `Preferences` read failure is swallowed.
  - Host-wide preview zero effects are not established.

### C09: Bash private staging custody and exit cleanup

- **Maps to.** ISM-INST-003 and ISM-INST-004.
- **Disposition.** `resolved and independently verified` within the recorded scopes. It was already strong at `f71fef6c`, and R0015 (#21, PR #85 `3b0e6141`) added the B1/B2 parent rules.
- **Enforcement.** `trusted_parent` (L97–150), `verify_root`, `guard_owned_path`, `cleanup_staging` (L208), and traps L221–223.
- **Verification.** Run 43162309006 at earlier bytes, and 43239081990/43239087955 at the final bytes. The macOS native staging suite was not re-run on the final bytes (registry finding (c)).

### C10: Bash asset download, validation, retention and extraction

- **Maps to.** ISM-INST-006 (Bash rows).
- **Disposition.** `implemented but not fully verified` on Apple hosts for the final bytes. Linux and earlier Apple bytes have SATISFIED rows 21-06…21-09 (issue 21).
- **Still open.** These are in the registry: no `curl` timeout, no declared digest or size check, no https requirement, `sorted(manifests)[0]`, and the whole-text `local=1` rewrite.

### C11: PowerShell shared cache and unpack lifecycle

- **Disposition.** `superseded by a different implementation`.
- **What changed.** The predictable `TEMP\SalahWidgetInstaller` cache (f71 install.ps1 L41–48, L303–380) is gone. It was replaced by per-attempt GUID roots (`Initialize-Staging` L693), explicit artifact records (`New-ArtifactRecord`), the single readiness predicate `Get-AdmittedArtifact` (L671) and unique-name publication `Publish-OwnedFile` (L1195). Built by R0015 (`00a08b69` … `b2718613`, merged in #85).
- **Maps to.** ISM-INST-004, 005 and 006.

### C12: Preset acquisition, hash rewrite and manual import admission

- **Disposition.** Split by host:
  - PowerShell: `resolved and independently verified`. `Download-Preset` L1467–1499 returns `$null` on any failure. It validates the canonical shape with `Get-CanonicalPresetShape` (L1426) and rewrites only the iframe token (`Convert-ConfiguredPreset` L1453).
  - Bash: `still implicit` for the rewrite scope. ISM-INST-006 records the whole-text `str.replace('local=1', hash)`, the unvalidated `SALAH_WIDGET_HASH` and line-ending normalisation.

### C13: Native generation output publication sequence

- **Scope.** Turns authored `src/native/*`, `real-sky/native-*` and `vendor/real-sky` into root `index.html`, `offline.html`, `config.js` and `builder.html`, plus `real-sky/core/**` and the bundles. A wrong output ships at the next merge to main.
- **Sources.** `tools/build_native.py` L1–114; `tools/native_core_horizon.py` L1–26; `tools/native_core_spectral_cache.py` L1–49 (new in R0027, #69); `tools/native_star_bootstrap.py` L1–28.
- **Dimensions.**
  - Input identity: vendor digests and authored sources.
  - `physical` flag read from `real-sky/checkpoint.json` (L9).
  - Write phase, in this order: core copy with 2 transforms (L12–16) → notices (L18–22) → `native-worker.js` (L35) → `native-sky.js` (L42) → star bootstrap check (L43) → `native-data.js` (L46) → root `config.js`/`builder.html` (L49) → `index.html` (L83) → CSS (L102) → `offline.html` (L109) → `build_moon` (L113) → report (L114).
  - Process exit code.
- **Transitions observed.**
  - Clean input: complete, rc 0.
  - Second run: byte-identical (probe, 0 diffs over 509 files).
  - Vendor digest drift in a transform: fails before that file is written. Earlier core files are already written (`tests/real-sky/native_spectral_cache_build_test.py` L137–155 asserts `optics.mjs` absent).
  - Manifest drift: fails at L43, after the worker and `native-sky.js` are written.
  - Moon failure: rc 1 with the root entries left unexpanded (probe C).
  - Hand-edited generated file: silently overwritten (probe A).
- **Guards.**
  - Digest guards in the horizon and spectral transforms (`ValueError`).
  - `assert` guards: `build_native.py` L70 and `native_star_bootstrap.py` L16, L21 and L28.
  - Exact-count guard on the config tag (L79).
  - **Unguarded** `replace(...,1)` calls at L72, L73, L74, L80 and L82.
- **Invariants.**
  - Generated output equals `build(authored)`. Holds at the baseline (probe).
  - The vendor tree is never edited.
  - Transform output digests are pinned.
- **Failure and recovery.** No rollback or staging. Recovery is a full re-run, which restored byte parity in the probe.
- **Enforcement.**
  - Documentation: AGENTS.md "CP9 source ownership" and R0027.md L262–275 (rebuild protocol).
  - Implementation: partly explicit.
  - Verification: unit tests and mutation controls for the two transforms (`native_spectral_cache_build_test.py`, 8 OK), plus recorded "build twice clean" claims in certificates (for example 6814244464). There is **no registered whole-tree parity test**.
- **Observed facts / hypotheses / unknowns.**
  - Observed: parity and idempotence hold at the baseline. A partial state is reachable and returns rc 1.
  - Hypothesis: an anchor drift at L72–74 would yield a "successful" build with the hooks missing. Not demonstrated with in-tree inputs.
  - Unknown: whether any executor ever ran with `-O`.
- **Disposition.** `implemented but not fully verified` (partly resolved relative to the original G01: the R0027 transform was added with fail-closed tests; staging and preflight were not added).

### C14: Moon generation preflight and expansion

- **Sources.** `tools/build_moon.py` L57–151 (HOST_UNITS gained `moon-install-guard.mjs` in R0021), `tools/compact_receivers.py`.
- **Preflight.** Both entries are validated before any write (L59–78). Asset, WASM, initial-receiver identity and ancestry are checked (L80–92).
- **Write order.** Worker (L108) → chunks (L113–116) → host (L131) → compact files (L132–133) → index and offline (L139–144) → `BUILD.json` (L150).
- **Duplicate expansion.** Rejected (L67–68; probe: direct `build_moon` on built entries raises). `tests/real-sky/moon_build_guard_test.py` passes 8 OK.
- **Stale outputs.** `moon/file-data/` is never cleaned, so an extra chunk survives a rebuild (probe B). `BUILD.json` records `chunkCount` but no file inventory.
- **Disposition.** `implemented but not fully verified` (unchanged from the original apart from HOST_UNITS).

### NEW-F-01: Frozen v1 verification

- **Source.** `tools/verify_v1.py` L18–92.
- **Behaviour.**
  - Default mode passes.
  - `--negative-control` passes, with its temporary directory redirected to scratch.
  - **`--check-pages` fails** with "New Jekyll configuration requires V1 inclusion review". `_config.yml` was added in `02ab7a93` (R0017, 2026-10-14), yet `docs/V1_PRESERVATION.md` L93 still prescribes `--check-pages`.
- **Enforcement.** Implementation: explicit. Verification: negative control exists. Documentation: partly stale.

### C24: R0017 Pages payload qualification

- **Sources.** `.github/workflows/r0017-pages-payload.yml`; `tools/verify_r0017_pages_payload.py`.
- **State.**
  - Trigger: `pull_request` to main. The job runs only `if: github.event.pull_request.number == 62`.
  - The verifier hard-codes `APPROVED=7fb3dd33…`, `ALLOWED` paths and a single `_config.yml` exclusion (L11–23). It asserts the regular-file total ≤ 1,000,000,000 bytes (L106).
  - The workflow is therefore an **inert retained instrument**: it is skipped on every later PR, and the verifier cannot be applied to main.
- **Disposition.** `no longer applicable` as a gate. The ≤1 GB constraint it measured is no longer re-measured (see FND-F-01).

### NEW-F-02: Pages deployment from main (`a commit to main is a deploy`)

- **States.** Merged commit → `pages build and deployment` (dynamic, legacy Jekyll) → built or `startup_failure` → served.
- **Actor.** The GitHub service. There is no repo-owned deploy workflow and no pre-deploy gate.
- **Observed.** The latest build is `363c3e53`. Served entries and installers are byte-equal to the tree (this audit). `294d2d37` had two startup failures before success, so the deploy is retried by the service.
- **Enforcement.** Documentation: AGENTS.md and README. Implementation: external. Verification: post-hoc public readback recorded in certificates.

### NEW-F-03: RLGWO delivery workflow (campaign governance machine)

- **States.** Candidate (work-order branch) → exact-tree review (independent review recorded in the contract) → owner approval for an exact head/tree/base → ordinary merge (no squash; "tree identical to the approved candidate") → Pages deployment → public byte readback → FINAL-CERTIFICATE comment (`<!-- Rxxxx-FINAL-CERTIFICATE:<sha>:<date> -->`) → issue closure.
- **Sources.** Certificates (for example R0013 6814244464: "Owner approval given for exactly this head, tree and base"; R0016 6828374683). R0015.md §7 "Root gates" (G15-ORDER/REVIEW/APPROVAL/STATE/DELIVERY/CERTIFICATE/LIFECYCLE).
- **Invalid and duplicate transitions observed.**
  - R0015 was **auto-closed** by a merge keyword and reopened (6816192574). This is a closure transition without a certificate, later corrected.
  - R0017 certificate withdrawn (6703510170) and later replaced.
  - R000D has a post-closure certificate correction (6792330574).
  - R0015.md L449 still says "`wholeContractComplete` remains false" and ES15-18 "not decided", while certificate 6828391831 (binding the same commit `363c3e53`) says those rows are resolved. The authoritative state lives in the issue comment, not the repo.
- **Enforcement.** Documentation: per-WO contracts. Implementation: human/agent process, with no tooling. Verification: independent review records.
- **Disposition.** `still implicit` (process-level).

### NEW-F-04: README review-first pin ↔ installer blob ↔ docs receipt coupling

- **Coupling.**
  - README L92–117 pins `a4c617eb` for both installers (an ancestor of main, not first-parent). The blobs there equal main (`e2e2640e`, `28cfdae7`).
  - `tools/qualification/installer_preview_docs.cjs` L18–20 pins README sha256 `b5df3f58…`, builder `873e8ded…` and config `719efed9…`. The baseline README equals `b5df3f58…`.
- **Consequence.** Any installer change requires re-pinning the README in the same change (R0015.md §5). That changes the README hash and invalidates the docs receipt, which then needs a new R0016 documentation run. ISM finding (d) already names this for wording changes.
- **Separate route.** The primary piped route (`/main/install.sh | bash`, builder L429–445) is unpinned and follows main immediately.
- **Disposition.** `still implicit`.

### NEW-F-05: Registered regression suites and the known-failure baseline

| Suite (run here) | Result | Notes |
|---|---|---|
| `node --test tests/*.test.cjs tests/*.test.mjs` (40 files) | 959 tests / 955 pass / 0 fail / 4 todo | Same as the R0013 certificate |
| `node --test tests/real-sky/*.test.mjs *.test.cjs` | 372 / 372 | |
| `node --test moon/tests/*.test.cjs` | 133 / 133 | |
| Python: `native_spectral_cache_build_test` 8 OK, `moon_build_guard_test` 8 OK, `native_horizon_build_test` 1 OK, `initial_source_association_test` 7 OK, `moon/tests/test_build.py` 2 OK | all OK | Temporary directories redirected to scratch |
| `tools/cp9/run_native_regressions.py --output <scratch>` | exit 1 | FAIL: r0001-date-sinks, r0009-date-selection, r0019-date-disclosure (all `el.style.getPropertyValue is not a function`), r0021-reveal (1), r0022-baseline-balance (7). INCOMPLETE: native-test-glob (936/940, 4 todo), r0022-lunar-consumers (SKIP_SUPERSEDED). This exactly matches the "known main failures, not relabelled" lists in R0003.md L364, R000F.md L349, R0021.md L449, R0026.md L310 and R0027.md L341 |
| `node tests/rlgwo-docs-contract.cjs` | exit 1, 64 cases / 50 pass / 14 fail | Registered as "(failing-set comparison)" in R0027.md L271 |

**The 14 rlgwo-docs-contract failures.** Every one is a stale-instrument case. The identical 14-case set fails on the `f71fef6c` file snapshot. At `fd2972ba` the instrument fails 25 of 40.

| Case | Count | Why it fails |
|---|---|---|
| `source: six real force branches…` (L245–270) | 1 | Pinned digest `5855c29a…` of the delegated native script; the current body hashes differently. Stale pin |
| `source: actual model-live negative and admitted synthetic wet…` (L372–395) | 1 | One `assert.equal(..., true)` returns false against the current weather reconcile functions. Which assertion is not isolated (unknown) |
| `docs: ARCHITECTURE.md / HANDOFF.md no positive query-only diagnostic recipe` (L421–423) | 2 | Query-form `?motion=full` / `?debugMotion=1` at ARCHITECTURE.md L132 and HANDOFF.md L152 |
| `docs composed: …` (L455–500) | 10 | Each requires tokens such as "Model estimate", "preceding-hour", "synthetic-present-v1", "Countdown unavailable", "stellar-background", "signed", "matching stellar projection", "Sunset date update unavailable", "Liquid glass" and "automatically". These come from docs commits `bdc806f0` / `89b29c47` on side branches (`codex/rlgwo-docs-final-20261002` and others) that were never merged to main. The instrument arrived on main through `3cf6ce2f` |

- **Disposition.** `still implicit`. The red baseline is used differentially, and that differential use is documented, but no machine-readable expected-failure manifest exists.

### NEW-F-06: Work-order-branch qualification workflows (32 files)

- **Triggers.**
  - 30 trigger on `push` to named work-order branches: `pro/r0016-effect-free-preview-20261111` ×17, `pro/r0017-corrective-windows-qualification-20261107` ×3, the R0007 branch ×2, and the R000B, R0013, R0015, B2, env-diagnostics and integration patterns.
  - 6 also accept `workflow_dispatch` (b2-staging-parent, installer-environment-observation, installer-preview-macos-python, r0013/r0015-integration-qualification, r0017-windows-qualification). r0017-windows-qualification is dispatch-only.
  - 1 triggers on PRs to main (C24, inert).
- **No workflow runs on `push` to main.**
- **Stale registrations.** All the named branches still exist on origin. Actions lists 36 workflows, including three no longer in the tree (`r0007-materialize.yml`, `r000b-recovery-materialization.yml`, `r0013-json-lexer.yml`) plus the dynamic Pages workflow.
- **Disposition.** These are inert leftovers of finished work orders, except as dispatchable re-qualification harnesses.

### NEW-F-07: Evidence receipts bound to source hashes

- **Pattern.** Receipts and tests pin exact sha256 values of sources. Examples:
  - `installer_preview_docs.cjs` L18–20.
  - `rlgwo-docs-contract.cjs` L270.
  - `tests/native-script-contract.js` SPLIT_PINS / RETAINED_INPUTS.
  - `tests/r0017-transport.cjs` legacy pin.
  - `verify_r0017_pages_payload.py` APPROVED.
  - `build_moon.py` L15–16.
- **Re-pin protocol.** R0027.md L262–275 says to re-pin after each rebuild.
- **Effect.** This guarantees that a receipt names the bytes it measured. It also makes every authored change invalidate unrelated pins, and stale pins become permanent "known failures" (NEW-F-05).

## 2. Historical-to-current reconciliation

| Original | RLGWO and evidence | Disposition |
|---|---|---|
| C08 | R0013 #19 (#84), R0016 #22 (#86) | resolved and independently verified (scoped) |
| C09 | R0015 #21 (#85; `dc4c251d`, `81c698be`) | resolved and independently verified (scoped; macOS not re-run on final bytes) |
| C10 | R0015 #21 | implemented but not fully verified (transport and timeout, digest residuals) |
| C11 | R0015 #21 (`00a08b69`…`b2718613`) | superseded by a different implementation |
| C12 | R0015 #21 (PS); Bash unchanged in scope | partly resolved |
| C13 | R0027 #69 (transform added); no staging (original G01 not done) | implemented but not fully verified |
| C14 | R0021 #33 (HOST_UNITS change) | implemented but not fully verified (unchanged residual) |
| C24 | none; PR62-locked | no longer applicable |
| CF01 failed partial adopted as cache | R0015. `Download-Asset` L1349–1368: GUID `.partial` candidate, `download-failed` throws, same-attempt reuse only through `Get-AdmittedArtifact`. Test `tests/install-powershell-transactions.ps1` L380–392 ("partial download is not a ready cache hit and healthy retry recovers"). Native run 43162309006 (transactions 28/28, mutations 22/22) and native6 43028305607 | resolved and independently verified |
| CF02 delete previous unpack before replacement | R0015. `Expand-ChromiumAsset` L1371–1393 extracts into a new `unpacked-<guid>` under the retained root; no delete. Mutant "publication collision preserves predecessor and complete partial" (`tests/install-powershell-mutations.py` L28–115) | resolved and independently verified |
| CF03 malformed preset returned | R0015. `Download-Preset` L1494–1497 returns `$null`. Test L479–487 ("malformed preset has no ready path or actual import handoff") | resolved and independently verified |
| CF10 malformed Firefox metadata → false absence | R0013. install.sh L409–453 and L549–551 (`parser-failed`); install.ps1 L1022–1087. Tests `install-discovery.py` L181/L209, `install-discovery.ps1` L59/L123, mutant "catch-to-absence" (`install-discovery-mutations.py` L29). Run 42978215112 and certificate 6814244464 | resolved and independently verified |
| R0014 (#20) PowerShell host parsing and release-asset selection | Closed 10-12 through PR48 (docs). R0013.md L146–151 treats it as a preservation constraint. No ISM entry models release-asset tier selection | unable to determine (code-level verification not in this lane's evidence) |
| EF01 stale instruments | R0017 #23 (`7214a2c8`): runner duration now monotonic (`run_native_regressions.py` L372/L392; measured seconds 0.05–24 against the original 20,406 s). Extraction rebound (R0017.md L133); r0010, r0011, r0017-transport, r0018, r001d, r001f, r0023 and r0025-lifecycle now pass. Still red: r0001, r0009 and r0019 with a new stale cause, r0021-reveal, r0022-baseline, and the docs contract (14) | partly resolved |

Original projection G01 (build staging and preflight before writes) was never done.

## 3. Findings

| Id | Title | Machines | Evidence class | Severity | Trace |
|---|---|---|---|---|---|
| FND-F-01 | Published Pages payload (estimate 1.91 GB, served) far exceeds the ≤1 GB bound that R0017 qualified at PR62 (0.898 GB). The verifier that enforced it is locked to PR62 | C24, NEW-F-02 | demonstrated (blob-size estimate plus served HEAD 200 for a 53 MB evidence ZIP); GitHub's limit-enforcement behaviour is not verified | medium: deployment risk and an evidence-scope regression; builds still succeed today | `verify_r0017_pages_payload.py` L95–106; `_config.yml`; workflow `if:` PR 62 |
| FND-F-02 | No automated gate on main or on PRs to main. All qualification is branch-bound or manual; "a commit to main is a deploy" | NEW-F-02, NEW-F-03, NEW-F-06 | demonstrated (trigger census) | medium (architecture, observability) | `.github/workflows/*.yml` `on:` blocks |
| FND-F-03 | Build guards implemented as `assert` disappear under `python -O` | C13 | demonstrated (probe D: manifest pin zeroed → normal rc 1 `AssertionError: manifest drift`; `-O` rc 0 "complete") | low–medium | `native_star_bootstrap.py` L16/L21/L28; `build_native.py` L70 |
| FND-F-04 | A Moon-stage failure leaves root `index.html` and `offline.html` unexpanded (no Moon), with Moon outputs from the previous build. Only rc 1 signals it | C13, C14 | demonstrated (probe C; re-run restored parity) | low–medium (a commit of that state would deploy a Moon-less widget) | `build_native.py` L83/L109/L113; `build_moon.py` L86–87 |
| FND-F-05 | Unguarded single replacements in the generator can silently no-op on anchor drift | C13 | plausible risk | low–medium | `build_native.py` L72–74, L80, L82 |
| FND-F-06 | Generated-parity and hand-edit detection rely on executor discipline. No registered test rebuilds and diffs the tree. Stale `moon/file-data` chunks are never removed | C13, C14 | demonstrated (probes A and B; parity itself holds) | low | `build_moon.py` L109–116 |
| FND-F-07 | Red regression instruments are retained as an undeclared "known failure set" | NEW-F-05, NEW-F-07 | demonstrated (identical 14/64 at `f71fef6c` and baseline; runner red set equals the documented lists) | medium (evidence: a new failure inside an already-red command such as r0001 is masked at the command level) | `tests/rlgwo-docs-contract.cjs` L245–500; R0027.md L271/L341 |
| FND-F-08 | `verify_v1.py --check-pages` fails at the baseline, but the documented recipe requires it | NEW-F-01 | demonstrated (run) | low | `verify_v1.py` L51–53; `docs/V1_PRESERVATION.md` L93 |
| FND-F-09 | Closure state is split between the repo and issue comments. R0015.md still says `wholeContractComplete` false while the certificate binding the same commit says resolved. Auto-closure, a withdrawn certificate and a post-closure correction occurred | NEW-F-03 | demonstrated (documents and comments) | low (observability) | R0015.md L413/L449; comments 6816192574, 6703510170, 6792330574 |
| FND-F-10 | README pin ↔ installer ↔ docs-receipt hash coupling multiplies the cost of any installer change; the piped main route is unpinned | NEW-F-04 | demonstrated (pins read) | low (architecture) | README L92–117; `installer_preview_docs.cjs` L18 |
| FND-F-11 | `IMPLICIT_STATES.md` omissions | ISM | demonstrated (absence) | low | See the list after this table |

FND-F-11 omissions, for the registry owner:
- **Release metadata and asset selection.** The R0014 tier order (`Get-LatestRelease`, Bash `select_asset`) has no entry.
- **Installer-bytes delivery.** Which bytes users run: main pipe against the pinned commit, `raw.githubusercontent` and the builder command. No entry.
- **Same-attempt Bash XPI reuse without revalidation.** Only mentioned inside 006.
- **Installer qualification workflows.** No entry for their lifecycle.

## 4. GDOPL inputs (Gradient Descent Over the Project Lagrangian)

Schematic only. Hard constraints in play: truthful evidence claims, canonical source and mutation ownership, safety and privacy boundaries.

| Interaction | Current q | Neighbour q' = apply(q, η) | Benefit / cost | Evidence | Class |
|---|---|---|---|---|---|
| Evidence volume ↔ deploy payload | Evidence committed under deployed `docs/` | η = extend `_config.yml` exclusions to evidence trees, or move evidence to another branch | Smaller payload, back under the modelled g (≤1 GB). Cost: github.io evidence links break; blob links survive | Before/after estimate 0.898 → 1.771 → 1.910 GB | demonstrated regression against the modelled constraint; the fix is a plausible improvement requiring verification |
| Merge ↔ deploy without gate | Manual qualification, then merge = deploy | η = a main/PR workflow running the registered suites, build twice with a diff, and `verify_v1` | Earlier failure detection. Cost: needs an explicit expected-failure manifest (FND-F-07) and CI minutes | Trigger census | plausible improvement requiring verification |
| Generator partial states | Write-in-place, assert guards | η = stage outputs in a temporary directory and swap after the Moon stage; replace `assert` with `raise`; count-check every replacement | Removes FND-F-03/04/05. Cost: a small builder diff that touches the generated boundary | Probes A–D | plausible improvement requiring verification (original G01, not taken) |
| Stale instruments | Retained red, compared by failing set | η = an explicit expected-failure ledger per case, or retire the side-branch-only "docs composed" checks | Restores signal. Cost: risk of hiding real regressions | f71 vs baseline identical 14; EF01 duration fix | partial demonstrated improvement (runner); remainder insufficient evidence |
| PS cache → transactional admission | Per-attempt roots, records, admission predicate | (taken) | CF01–03 removed. Cost: install.ps1 grew from 614 to 1,741 lines; 22 installer workflows | Diff, tests and native runs | demonstrated improvement |
| Hash-pinned receipts | Exact pins everywhere | η = bind receipts to a manifest in one place | Fewer cascading re-pins | Re-pin protocol in R0027.md | incomparable |

Relation to the original GDOPL_PROJECTION: the installer and EF01 directions were taken, with evidence. The build-staging direction (G01) was not taken. The Pages-payload constraint the original treated as already explicit (C24) became inert.

## 5. Coverage

**Read fully:**
- `IMPLICIT_STATES.md`
- `tools/build_native.py`, `tools/build_moon.py`, `tools/native_core_horizon.py`, `tools/native_core_spectral_cache.py`, `tools/native_star_bootstrap.py`, `tools/verify_v1.py`
- `r0017-pages-payload.yml`
- Installer regions: `Download-Asset`, `Expand-ChromiumAsset`, the preset functions, `Get-FirefoxExtensionStatus`, `firefox_status`, eligibility
- R0013.md L1–240
- The certificates for R0013, R0015 and R0016 (heads only)

**Sampled:**
- R0015.md (§3–7), `r0015-artifact-transactions.md`, `verify_r0017_pages_payload.py` L1–60, `installer_preview_docs.cjs`
- The `on:` blocks of all 32 workflows
- `tools/qualification/README.md` headings, `rlgwo-docs-contract.cjs` failing cases

**Not examined:**
- `compact_receivers.py` internals
- `tools/qa/**` and most of `tools/qualification/**`
- R0016.md detail
- Bash staging code beyond the registry
- Native or CI execution

**Runs:** all the suites in the NEW-F-05 table; `verify_v1` in three modes; the build twice plus probes A–D in a disposable copy; the docs contract at `f71fef6c`/`fd2972ba` snapshots; the public readback (4 files); `gh` read-only queries.
