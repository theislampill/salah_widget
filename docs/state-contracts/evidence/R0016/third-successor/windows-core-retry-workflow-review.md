# Windows PS7 companion retry workflow — FINAL PASS, bounded routing review

## Exact reviewed inputs

Root requested review of the isolated workflow routing delta. The collector and receiver changes are being reviewed separately by root.

| Input | Bytes | SHA256 |
|---|---:|---|
| Baseline workflow | 4,760 | `c0ebf7a877a91fd8c29357dd7a812b0604b483f62f596a14a21d0f6fd0cbd349` |
| Proposed workflow | 4,737 | `f73af299fa919d12fe1189e134f3280bdc2e2c10eb797ce189e28a49478d6a98` |

The complete byte diff contains exactly three unique literal replacements:

1. Title becomes `R0016 PS7 normal-companion retry`.
2. The sole push branch becomes `pro/r0016-windows-normal-retry-20261112`.
3. The host matrix becomes `[ps766]`.

Applying those three substitutions to the original bytes reproduces the proposed bytes exactly. No other YAML, command, guard, path or hash changes.

## Findings

**No concrete defect found within this routing scope.** The dedicated branch and single PS7 cell match the requested retry. The existing job command still invokes the core launcher with the event's exact `${{ github.sha }}`; core and companion semantics remain determined by the separately reviewed source at that checkout. The unchanged runtime acquisition selects the exact PowerShell 7.6.6 archive and its existing SHA256 gate. It occurs before selected PowerShell startup.

Permissions remain `contents: read`, checkout credentials are not persisted, and sparse input paths are byte-identical. The owned C-volume profile preparation, common core/archive/upload paths, `always()` archive and upload steps, no-follow archive command, 140-minute job ceiling, and `cancel-in-progress: false` remain unchanged. Concurrency is qualified by `github.ref`, keeping the retry branch separate from the primary branch. The unchanged conditional PowerShell selection resolves the sole `ps766` matrix cell through `INSTALL_TEST_PS7`; the retained `ps51` branch is unreachable in this workflow's matrix.

The primary workflow at immutable commit `3e28cd3f565de3c0e09bd81d69d78c37526487d5` was read directly with `git show` and is byte-identical to the original two-host baseline. Root can retain that primary workflow while placing this variant on the owned retry branch.

## Verification

Fifteen inert checks passed: exact baseline/proposal hashes, uniqueness of all three replacement sites, complete byte equality after the replacement allowlist, parsed sole branch and matrix, unchanged job steps/settings, unchanged strategy policy, permissions/path/concurrency equality, exact commit argument, retained archive/upload behavior, runner/ceiling, syntax-only parsing of both embedded Python expressions, and unchanged primary two-host workflow. YAML was parsed with `BaseLoader` to preserve the literal `on` key. No embedded expression, project source, PowerShell, installer or workflow was executed.

`verification.json` records the individual checks. `reviewed.patch` and both exact input files are retained. `diff` exited 1 because the intended three changes exist; the complete verification command exited 0.

## Scope and independence

Requested model: inherited GPT-6 Astra Pro, no override. Actual runtime-reported model: GPT-6 Astra Pro. `authoring_context_reuse: no` for this root-authored three-literal change. I previously authored the original core route/workflow and disclose that relationship; this review makes no new independence claim for the unchanged baseline or the collector `555e606b…`.

Disposition is **FINAL PASS for the exact isolated workflow routing delta**. Root retains source review, publication and dispatch authority. This report grants no native result, no change to the original PS5.1 outer FAIL, no reinterpretation of its separately received 75+18 observations, and no overall R0016 acceptance. All outputs are in this review's own scratch directory. No shared source or remote state was changed, and no process remains running.
