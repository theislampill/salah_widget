# Independent R0013 native run 3 — Apple and Linux receipt review

Reviewer: `/root/r0013_review`. Ordinary engineering review; no lifecycle or merge authority.

**Disposition:** No new blocking source or instrument finding in this bounded receipt review. Native Apple execution supports the original Bash 3.2, full entry, detector and mutation requirements at the exact candidate. Whole-contract completion remains open.

## Exact binding

- Commit: `6aefcd06673fc5d6dc76a33530d47320320b0d4f`
- Tree: `f112393d4d4713a95828c3af9e7b8e6b614f4bc4`
- Sole parent: `eda44916bd107a64c687efd82de4e5c141be4fd1`
- Bash SHA256: `609ecb0bb6924eccee5c311b77f0d513f0e78c3462c7fa5b15b1fd38694a5b22`
- PowerShell SHA256: `a67ac0c6190b3027a4ca31a1703df76b66558582e29b583bd15afe3da17bb7a4`

I reconstructed the immutable commit/tree/blob hashes, matched 17 previously reviewed source and instrument files, compared both received zip/tar digests, and compared every extracted top-level receipt byte-for-byte with its regular tar member. The candidate delta contains six reviewed test files and 70 retained evidence files; neither installer changed. No archive extraction, installer execution, source edit, branch change, remote write or governor action was performed.

## Native evidence received

| Suite | Actual Apple Bash 3.2.57 | Linux Bash 5.2.21 |
|---|---:|---:|
| install-bash | 26/26 | 26/26 |
| install-entry-bash | 25/25 | 25/25 |
| install-discovery | 76/76 | 76/76 |
| install-detectors | 12/12 | 10/10 |
| install-discovery-mutations | 13/13 | 13/13 |
| install-original-mutations | 8/8 | 8/8 |
| install-builder | 4/4 | 4/4 |

The discovery mutation total includes twelve mutants plus the exact-source healthy prerequisite. Modern Bash reports both Apple-specific empty-array cases as inapplicable and does not credit them as passes.

Apple acquisition records identify macOS 15.8.2, arm64, `/bin/bash` 3.2.57, UID 501, GID 20, the actual native tool paths, and independent output and fixture-parent filesystem receipts. Both volumes resolve to APFS `/dev/disk2s5`; all acquisition commands exited zero. The effective fixture parent is an owned mode-0700 directory under `/private/var/folders`, with physical path, device and inode recorded.

## Repaired native failures

### Intended selected profiles are now demonstrated

The raw full-entry transcript identifies Chrome/Default as index 1 and Firefox/fixture profile as index 2. Both asset-family metadata calls occurred, both manual assets were retained, and two later confirmations were consumed. The independent boundary control observes native Chrome and Edge executables under `/Applications`, proves the fixture boundary rejects both, and keeps ordinary `/bin/cat` discovery available.

The discovery receipts identify known Firefox `profile-0` at index 1 with exit 0 and 19 intercepted effects. Unknown Firefox `profile-1` is now explicitly index 2 with reason `metadata-malformed`, exit 1, zero effects and an unchanged subject snapshot. The earlier false identity credit is therefore not inherited.

### Zero-exit empty-array mutations retain their actual behavior

For each browser family, the archived healthy script gives exactly one no-profile fallback row, exit 0 and empty stderr. Its mutant differs only by removal of the selected family guard. Both mutants parse successfully and exit 0, but emit the exact `profiles[@]: unbound variable` diagnostic, produce no `COUNT` and no rows. The repaired oracle credits that precise named failure, not a fabricated nonzero exit. Raw script hashes match their receipts.

The six other detector mutation pairs also retain healthy native results and changed named outcomes: mapfile absence, current-shell state lost through a pipeline, and literal backslash loss, for both families. Twelve discovery mutants and eight original mutants were independently rebound to archived bytes, exact adverse case names and unaffected healthy controls.

## Readiness and scope

I verified 24 raw per-fixture nonce files and acquisition files: 23 complete-entry cases plus the browser-lookup boundary control. Nonces are distinct, paired with positive numeric PIDs, and emitted after all interception functions and before source evaluation. Pipe cases have the expected multiple process markers. The missing-nonce control executes a healthy preview but correctly rejects qualification as `BOOTSTRAP_BLOCKED`.

Fifteen discovery full-entry observations separately record distinct nonce/PID values, native ownership/identity, selected identity where applicable and effect counts. Their imported entry-helper fixtures live outside the top-level discovery fixture root and are not included as raw subtrees in the received archive. I accept their exact-source actual-test assertion records within that scope; I do not claim independent raw marker/transcript verification for those fifteen cases.

## Full denominator retained

The published contract matrix is byte-identical to the recovery matrix and retains all 12 original parent rows, 7 residual children and 14 November amendment rows. The JSON report maps every row to received engineering evidence or a remaining gate. Original Apple detector/entry/mutation rows now have actual native evidence; final documentation and delivery rows remain open.

## Findings and remaining gates

No new Critical, Important or Minor defect was established in this bounded receipt review. `R13-NATIVE-01` and `R13-NATIVE-02` now have independently received native corrections. The Apple acquisition portion of `R13-REV-03` is supported; Windows is a separate gate. Earlier strict JSON, duplicate-key and mutation-attribution repairs remain bound to unchanged product source.

- Receive/classify actual native Windows PS5.1 and supported PS7 complete-file entry; retain version-specific non-discriminating mutation applicability without crediting survivors.
- Publish final docs-only commit pinning both Bash and Windows examples to the qualified exact source; review exact ASCII/byte/policy/manual/cache/newline guidance and changed copy paths.
- Verify final public raw script bytes, rendered documentation, builder/generated/copy command behavior and delivery commit bindings on the required surfaces.
- Retain original failed runs and invalid local premise; complete any necessary R15 interface-native UID proof without claiming R15 whole-issue closure here.
- Parent must establish campaign predecessor/currentness gates and exact owner approval before merge; final integration/publication checks and closure authority remain outside this report.

The existing invalid local `/tmp` foreign-owner premise remains retained and receives no new credit. Actual native helper success is not substituted for the separately commissioned R15 dedicated UID proof. Campaign order, exact owner approval, final merge/integration currentness and closure are parent-owned decisions.

Detailed evidence, full per-row scope, archive member bindings and the 533 receipt checks are in `native-run3-apple-review.json`. These are review consistency checks, not additional native test executions.
