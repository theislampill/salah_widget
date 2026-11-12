# Independent Ubuntu22 full-native proposal review

Disposition: **PASS within the frozen two-file source-review boundary.** No native admission or product acceptance is supplied. This reviewer executed neither candidate code nor a native test, and made no shared mutation, publication, dispatch or policy change.

## Exact packet

Packet `/tmp/r0016-third-20261111/work/root-linux22/candidate-1` has manifest SHA256 **`631ae5bb6f7e80abc83eb88f5902db171a1d651e74563215f1218f6663bada39`**. All eight listed regular files match their size and digest. All five base files also match their exact Git blobs at current published commit **`2f5b5d58b494b37d285ab2130c2e6cafd1563a57`**.

| Proposed input | SHA256 |
|---|---|
| `installer_preview_linux22_prerequisites.py` | `adb7c47a6416b51bf96b6647e500bfba4e2d206a50a408a0e331f16d61ea9161` |
| `installer-preview-linux22-native.yml` | `ae95cd0c4911111402ebe1b346de20a7cfcc5e317cdbfae8541159f9b2a6ccf0` |
| Unchanged full native collector | `9732e7687ced927be21bdca8f9fae08e29c7104d0119fe435ea74dcc86a1a46f` |
| Unchanged preview fixture | `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00` |
| Current product input | `d19ed5d90e1faf0d9ac66415814a3a68e28c6ae61730acd4eaef1b9588830cc5` |

## Prerequisite helper

The entire 6,986-byte proposed helper is exactly the original reviewed helper after two text mappings: `noble` to `jammy`, and `24.04` to `22.04`. The whole AST is otherwise identical after normalizing those string literals.

The native Ubuntu/Jammy and amd64 guards remain. The selected sources are signed official Jammy, Jammy-updates and Jammy-security repositories using the existing Ubuntu archive keyring. Isolated APT configuration, path validation, TLS verification, expiry checks, insecure/unauthenticated repository refusal, zero retries, bounded command budgets, original stream capture and fail-closed completion are unchanged. The original Noble helper is not edited or invoked on the Jammy host.

This change addresses the concrete wrong-release prerequisite problem identified during native receiving. It does not alter an AppArmor policy or sysctl, grant privilege to a preview subject, or remove an existing containment guard. The existing signed package preparation still uses the original scoped sudo acquisition route; it is not a newly privileged installer route.

## Workflow and complete product path

The entire parsed workflow equals the original full Mac workflow after the declared adaptations: honest Ubuntu22 display/job/runner/OS identity; distinct workflow/concurrency/artifact names; the Jammy prerequisite step and sparse path; the original Linux-owner fixture trigger; and the already reviewed preparation-evidence packaging block copied from the Linux diagnostic with only its preparation directory name changed.

The workflow keeps the owner branch, read-only contents permission, both exact action pins, `${{ github.sha }}` checkout, depth one, no persisted credentials, twenty-minute job budget, complete product/preset/builder/test sparse inputs, and thirty-day artifact retention. It has no continue-on-error, alternate uncontained caller, new environment override or suppressed failure path.

After preparation it invokes the original full collector with **`--expected-os Linux --phase r0016`**. That retains all inherited Linux command groups, including `install-linux-owner`, plus the original Bash preview fixture and all its helpers, complete entries, negative controls, normal controls and mutants. The preview uses its existing original unshare/bwrap route, read-only host binding, owned write binding, seccomp observer and bootstrap assertions. A failed bootstrap still supplies no preview acceptance. The one Darwin-only literal-absence row does not silently become a Linux obligation or inflate its denominator.

The Linux owner fixture remains the existing distinct-UID supervisor/consumer test; the collector has not been changed to execute production as a root subject. Its existing ownership fixture/export behavior is separate from preview containment and unchanged by this proposal.

The new concurrency group is **`installer-preview-linux22-native-${{ github.ref }}`**, with `cancel-in-progress: false`. It differs from both the original queued Linux namespace group and the current-source diagnostic group. The new artifact name is **`r0016-native-Linux22-${{ github.run_id }}-${{ github.run_attempt }}`**. The earlier Ubuntu24 failures and stale queued run remain untouched.

Always-run packaging preserves the entire original product evidence tree without following archive symlinks, and also retains the original preparation files and inventory. It excludes only the three explicitly named disposable APT directories. Its directory creation allows a failed preparation receipt to survive even when qualification never started; that archive creation is not a product PASS. Collector success still requires actual terminal command results and their original row flags.

## Recommendation and limits

The original R0016 contract requires native hosted Linux evidence without fixing its distribution release. The separately scoped Ubuntu22 proposal is therefore a material next-host observation that preserves the contract and original failures. It must report the actual host honestly. Neither runner availability nor a result on Ubuntu22 can establish successful Ubuntu24 admission or explain the prior policy refusal.

All **23 independent data/source comparisons passed**. `verify_source.py` and `verification.json` retain the exact comparisons; no candidate code or additional local fixture campaign was executed. Root is separately verifying current official runner availability and owns the proposed one-run authorization, publication and later original artifact receiving.

No blocking source issue was found in this packet. Actual preparation, Linux containment, normal behavior, negative discrimination and bounded cleanup/capture remain questions for the authorized native run. Product qualification and whole-contract closure remain outside this source-review PASS.
