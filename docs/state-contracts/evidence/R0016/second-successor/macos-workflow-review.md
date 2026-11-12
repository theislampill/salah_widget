# Independent Mac workflow publication-candidate review

**State: FINAL. Disposition: PASS for the exact two-workflow routing candidate and its stated dependency identities.** This is a bounded routing/code review, not a native qualification result, authorization to publish/dispatch, whole-contract readiness or closure authority.

Reviewer: `/root/product_recovery`; requested and actual model `gpt-6-astra` (actual self-report); authoring-context reuse **no**. Applicable AGENTS, audit-playbook Finding Row Contract and child-agents instructions were read. Both complete proposed workflows, the exact generic-workflow diff, author notes/manifest, the unchanged native runner's Darwin route and its input dependencies were inspected. No product, native, PTY, namespace, shell fixture or workflow was executed. No shared source or repository was modified. Read-only YAML/AST/hash/routing checks were performed, with evidence written only in this reviewer's scratch.

## Exact binding

| Candidate file | Bytes | SHA256 |
| --- | ---: | --- |
| `.github/workflows/installer-native.yml` | 5655 | `0b452ab41760f61513aba86629188604959f9a54f767d1e1b6a440e333820104` |
| `.github/workflows/installer-preview-macos-native.yml` | 2459 | `eaaea01410c8ed9a3733a110c756edd33d7c045afd6987f929b59f5429b89e62` |

The existing runner remains `9732e7687ced927be21bdca8f9fae08e29c7104d0119fe435ea74dcc86a1a46f`. Both the provided dependency snapshots and live source independently match reviewed `install.sh` SHA256 `dbd91b67828791e35efb042e6954990c45ff579ee13f550d1d8aa70c7b2f32f4` and preview harness SHA256 `8babcffa108f777fa3add01f39a4e26b537f5e1521ed8d4b490c171153b3817e` (Mac candidate3). These source dependencies are root-authored; this review does not rewrite or newly author them.

## Routing and native scope

The generic workflow differs from baseline `9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196` only by removal of the R0016 push branch and addition of the explanatory comment. Structural YAML comparison confirms every job, path, command, budget and remaining R0013/R0015 branch is unchanged. The new workflow has exactly one Darwin job on `macos-15` and invokes the existing full runner with `--expected-os Darwin --phase r0016`. It supplies no suite subset, environment gate bypass, new sandbox allowance, fallback or timeout increase.

The unchanged runner checks actual host identity and native acquisition facts, requires Apple `/bin/bash` version3.2, sets `SALAH_TEST_BASH=/bin/bash`, and runs nine command groups: Bash helpers, full Bash entry, discovery, detector compatibility, discovery mutants, original behavior mutants, builder serialization, native staging and complete preview. Existing source-bound, typed result and mutation checks remain in those consumers. The workflow neither turns the historical PTY diagnostic into native product PASS nor invokes Windows product qualification. Windows and Linux product acceptance remain pending separate obligations.

The checkout step is structurally identical to the original native POSIX checkout, including pinned action, exact `${{ github.sha }}`, depth1, no persisted credentials and all sparse source/test inputs. Both workflow and original POSIX outer budget are20minutes. Evidence packaging/upload both use `always()`; packaging rejects missing collector output, retains fixture names without dereferencing symlinks, and upload errors on a missing artifact. The archive is distinctly named by Darwin, run and attempt. The packaging Python parses without execution.

## Independent routing checks

I parsed all current repository workflow definitions, overlaid the exact two proposed workflows, and evaluated their declared branch/path filters for the scoped candidate changes. For these literal and simple-glob rules, the retained check implements their matching directly. Results:

| Changed set | Selected workflow on R0016 |
| --- | --- |
| Linux stage1 three diagnostic files | Focused Linux namespace diagnostic only |
| Proposed product/test files plus both Mac routing files | Dedicated Mac native workflow only |
| Each of the14 declared Mac inputs individually | Dedicated Mac native workflow only |
| Windows-only source, preview, native coverage, shared Windows support/acquisition fixtures | No Mac or generic native workflow |
| Same product/Mac changes with generic R0016 branch removal omitted (negative control) | Both generic native and dedicated Mac workflows; generic would include Windows |

The14 Mac paths consist of the product Bash file, nine directly consumed test files, builder/config files, runner and new workflow. Discovery's Bash entry import and both mutation drivers' consumed Mac tests are included; preview's normal/NoOpen adapter also uses the included entry harness. The runner hashes additional checkout files for custody; that alone does not make Windows-only sources a Darwin behavioral input. The tested Mac consumers do not read the repository canonical preset file as their fixture source; generated owned preset fixtures remain within the included tests. The original sparse `/presets/` population remains unchanged.

R0013 and R0015 generic native routing still selects the existing generic workflow for their original source changes. The focused later Windows host diagnostic is not repurposed. Stage1's original Linux observer pin must be preserved by its separate earlier commit. This stage must include the reviewed product/Mac dependency bytes; a future changed diagnostic helper/workflow would require explicit pin reconciliation before rerunning it against the new preview harness.

## Findings and limits

**No blocking finding in this exact bounded routing candidate.** Native execution may still reveal a product, instrument or environment failure. Successful YAML/routing checks do not establish native Mac behavior, classifier correctness outside the reviewed changes, Windows qualification or any of the final46-row acceptance/delivery obligations. The prior bounded candidate3 review and current source identities remain distinct from a future actual native receipt.

Root owns implementation/publication. Restore or explicitly route later Windows qualification when its reviewed instrument is ready; keeping that platform pending is part of this candidate's stated scope, not a silent removal from the denominator. Rollback may remove the new Mac workflow and restore the generic branch entry, but restoring that entry also restores its Windows trigger and must be an intentional root action. Any changed workflow/dependency identity needs a new bounded check.

Evidence: `mac-publication-routing-checks.json` retains exact candidate hashes, structural checks, all14 input results, positive routing sets, the missing-reroute negative and both unchanged generic branches. No native subject executed.
