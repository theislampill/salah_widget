# Independent Linux successor source review

Disposition: **PASS within the two-file diagnostic source-review boundary.** Native execution and product acceptance are not supplied by this report. The reviewer did not modify the shared repository, publish, dispatch, retry, cancel, or change host security policy.

## Immutable inputs

The packet `/tmp/r0016-third-20261111/work/root-linux-successor/candidate-1` has manifest SHA256 `ff2cd6d1ed72fc3907d3e670656043df134e080a93ee3209085b985ccf42ed19`. Every one of its seven listed files matches its size and SHA256, and is a regular non-symlink file.

| Input | SHA256 |
|---|---|
| Proposed successor probe | `8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328` |
| Proposed successor workflow | `16df198aa655a2df5c5bb60b2eb1d87321c050d5eac957856a50a7f38460a2bd` |
| Original probe | `eb4fda18db9423f461f74cc8212ff417af02ca0d85c9642390988a0d0419243b` |
| Original workflow | `a9dbcb4152388ded002aa1635205d233e43320341d774ea9ee4c8e8e643c1813` |
| Current harness | `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00` |
| Prerequisite acquisition source | `4ddf713e6ae1a8112f0c96fd756e9dc143109dbecd3faa32afa3d1e43d4d54c4` |

The four base workflow/probe/harness/prerequisite files also match their exact Git blobs at published commit `f8d3db2d6d6d84f63bf8d79cf52c6977558cb105`. The current source identity is genuine; no old-checkout/current-GITHUB_SHA substitution is proposed.

## Exact scope and executable entry

Replacing the single original `HARNESS_SHA256` assignment (`5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760`) with current `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00` reconstructs the entire proposed probe byte for byte. The entire AST also matches after neutralizing that one constant. Thus both routes, guards, snapshots, clocks, capture limits, pidfd cleanup, assessment, and negative classifications are preserved without a second behavioral delta.

The complete original and current harness prefix through the `--sandbox-child` entry is 5,467 bytes / 105 lines and is byte-identical and AST-identical. Its SHA256 is `05a6529d6154f0176420b16b6f5457f741627e21a3b9abbcd2d7b44836e1c98a`. This comparison includes the initial imports, `digest`, `sandbox_child`, `positive_child`, and the early dispatch, rather than only the child function body. The child exits or raises without proceeding into ordinary installer fixture acquisition.

The workflow is exactly the original after five specified text mappings: display name; workflow filename; probe filename (all three occurrences); concurrency group; and artifact name. It keeps native `ubuntu-24.04`, the ten-minute job deadline, both pinned action versions, read-only contents permission, exact `${{ github.sha }}` checkout, depth one, disabled persisted credentials, the three-file sparse checkout, prerequisite invocation, always-retained original evidence, and thirty-day artifact retention. The sparse checkout does not acquire installer product source.

The new group is `installer-preview-linux-namespace-third-${{ github.ref }}`. The original group and original workflow remain unchanged in the packet. This is an independently identified current-source diagnostic, under the root's stated authorization for one execution. It is not a retry or cancellation of run `43098061480`.

## Retained containment and negative behavior

Because every other probe byte is unchanged, the original `original-unshare` and `packaged-bwrap` routes retain their exact namespace commands, read-only root binding, owned write binding, no-new-privileges and seccomp requirements, non-root/equal-UID guard, root-owned prerequisite binding checks, thirty-second subject budget, five-second cleanup budget, and one-megabyte stream limit. There is no sudo subject route, permissive namespace fallback, security-policy modification, or PATH masking.

Natural terminal success, readiness/PID/nonce/ancestry and namespace joins, owned writes, outside-write denials, TCP/UDP denial receipts, complete stable snapshots, and cleanup still jointly constrain the containment control. Missing transport telemetry is not interpreted as zero attempts. Late terminal completion, capture overflow, controller error, and incomplete cleanup remain negative or incomplete outcomes. A completed discriminator acquisition may retain diagnostic-negative route outcomes and still executes zero product rows; its workflow status cannot establish product qualification or identify the precise host policy responsible for a denial.

## Independent verification

All 18 source/custody checks passed. The original seven receipt/inventory tests and five focused lifecycle checks were copied unchanged into owned scratch and executed against the exact successor bytes, presented under the historical import filename expected by those tests. The candidate's main function was not executed. All process launches, pidfd signals, and controller operations used by the focused checks were mocked; these checks supplied no native namespace or native product evidence.

The twelve checks retain coverage for missing transport records, wrong namespaces/PIDs, cleanup/signals/return codes, incomplete or changed snapshots, late-file mixed-time acquisition, identical common bind arguments on both routes, late terminal exit, forced-positive assessment defeated by capture/controller/cleanup failure, and final cleanup continuing across held descriptors after kill/close errors.

## Evidence and limits

`source-receipt.json`, `sandbox-child-prefix-receipt.json`, `probe.diff`, `workflow.diff`, `inert-receipt.json`, and `inert/` preserve the mechanical comparisons and original test streams. All are under this review directory. The separate prior currentness report retains the original queued-run and UID-map-failure evidence. This source review did not refresh the old run's API status and does not infer a queue cause from another runner's success or from a GitHub incident.

No blocking issue was found in this bounded proposal. The root remains responsible for publication, the one authorized execution, original artifact acquisition, and later evidence-bounded disposition. The stale original run and the original UID-map failure remain unresolved historical facts; this PASS does not erase either.
