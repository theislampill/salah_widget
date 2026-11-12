# R0016 third successor: independent native ApplePython artifact receipt

**Disposition: PASS for the bounded original-artifact receipt and diagnostic differential. GAP for installer product qualification and complete global effect/transport-attempt proof, which this source-free run does not supply.**

This lane did not author the probe or installer, modify the shared repository, execute archived code, change host policy, dispatch a run, or mutate GitHub. It read the original ZIP, safely materialized regular members only in its own scratch directory, reconstructed the selected core with Python AST parsing only, and compared the original bytes with immutable Git objects and retained API response bodies. This is a receiving report, not a formal audit-assess governor disposition, readiness decision, whole-contract acceptance, or closure authority.

## Identity and source joins

| Item | Independently received value |
|---|---|
| Run | `43120106311, attempt 1, push event; retained API status completed/success` |
| Published commit | `63bcef3b754ea85b784ba788807818f29b2c11c2` |
| Commit tree | `142a34a85c449de833b0fecd1b025681a7d3dbeb` |
| Commit parent | `968a97283bc4f41e01f1779bf6867618cca85100` |
| Artifact | `13900750800; r0016-python-Darwin-43120106311-1` |
| Original ZIP | `112981 bytes; SHA256 2a7e6c3328a99ba7434437bcb4bc1aca6e147d1c479c98b3694b222f1706e6a7` |
| Inner TAR | `123651 bytes; SHA256 2d649f08f4b80141b0b6ea70b04743a28e5068c443235a775c62cc08a46d94cd` |
| Frozen manifest | `05aa190d89068811f6b13ef2ecf938fea084912e2b67ccef3c9ccf16646ca713` |
| Probe source | `f24a7020e9d59bcd6e8f632d6ccf9ec41057ee79ebc30a454ca4fa9f1fa6032b; 32067 bytes` |
| Workflow source | `7a2aeb313c8867a27db8ae46926fefd288e173ff072eea5a287ba77f59a9290b; 3755 bytes` |
| Whole harness | `ee209dac5cc2c635315557fa3ab8990bc994a5e6cd33367c565291392c35c306; 55920 bytes` |
| AST-selected bootstrap core | `02e7934793b6e371c63cc9af1cf377cc881801fa94463059c1bb7276e71e9e5f; 26552 bytes` |
| Frozen Python subject | `a0530b6dd87df43c37ee1aee1f259ebcb25daac84742e7559c5b375a6818b43f; 435 bytes` |

The retained run API body identifies the exact commit and workflow path `.github/workflows/installer-preview-macos-python.yml`; the retained artifact API body joins artifact ID, run ID, head SHA, name, byte count, and SHA-256. The actual ZIP matches that digest. The API success state earns no product credit. The ZIP passes CRC verification. The TAR has 263 members: 182 regular files and 81 directories, no symlinks, hardlinks, unsafe traversal paths, or duplicate names. All 181 inventory entries match both length and SHA-256; the inventory file itself is the sole intentionally unlisted regular file.

Immutable Git object reads establish the commit tree/parent and source bytes. The archived full harness is identical to the published harness. Independently selecting the 12 named functions and two constants from its AST exactly reconstructs the archived bootstrap core. The archived Python subject exactly equals the probe’s literal PROGRAM. Every file in the candidate2 source-freeze manifest matches its declared size/hash. Static review of the selected core, probe, and sparse checkout shows that this diagnostic reads the harness and fixture metadata, not installer source. The product-source inspection below was performed separately by this receiver and is not part of native execution.

## Exact host and executable identity

Native capture reports Darwin kernel 24.6.0, macOS 15.8.2, arm64, and Apple `/bin/bash` 3.2.57(1)-release. The original Bash version stream agrees with host acquisition. Nine recorded executable/source bindings are byte-for-byte identical before and after the experiment.

| Role | Path / physical mapping | Bytes | SHA-256 |
|---|---|---:|---|
| physicalPython | `/Applications/Xcode_16.4.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9` | 102352 | `5c5950c62eee5fd227a67e4bdfcde81c9add59799bba0949635f3d5ba9661c26` |
| shim | `/usr/bin/python3` | 118864 | `8291fbbbaa75761bb649970a16af2ef84b4afd5da0bc133f4d8915f0f2f63e98` |
| observer | `/opt/homebrew/opt/python@3.15/bin/python3.15 → /opt/homebrew/Cellar/python@3.15/3.15.2/Frameworks/Python.framework/Versions/3.15/bin/python3.15` | 34640 | `fe4fd6c475964c108a2f4b105dcb46f849f4fc2c84d1b46f37443b0eb492fc38` |
| xcodeSelect | `/usr/bin/xcode-select` | 119104 | `d2ced6340d9f93caf086ae40c5b69ccbcc11855a25ce46f1f522b6053fc21de4` |
| xcrun | `/usr/bin/xcrun` | 117392 | `274eb256dc4af66bef7737a28b330713105eb67f362338135e932ae3ded9ad76` |
| bash | `/bin/bash` | 1310224 | `87bec2413226d37381edf499a64277c9d9bcb9fdae555a844bf0480b48b6c3e3` |
| sandbox | `/usr/bin/sandbox-exec` | 102560 | `127f88fe61d5b4802806ed8e1b258b421b11af2a751fe42e49102c1440cd28c5` |

All five Python payloads report Python 3.9.6 and the same recorded physical image hash. Shim payloads report `/Applications/Xcode_16.4.app/Contents/Developer/usr/bin/python3`, which the captured binding resolves to the physical `.../Python3.framework/Versions/3.9/bin/python3.9` image above. Direct cases launch that physical path. The observer is the separately selected Homebrew Python 3.15.2; it is not substituted for the Apple subject interpreter. Native executable binaries are not archived, so receiving verifies the recorded native path/hash joins and before/after stability; it cannot independently rehash the historical host images.

## Five original Python captures and contained selector

| Case | Launch/payload PID | stdout bytes | stderr bytes | Denied cache diagnostics | First terminal observation (s) |
|---|---:|---:|---:|---:|---:|
| baseline-shim-before | 1240 | 736 | 288 | 2 | 0.935003334 |
| baseline-direct | 1265 | 784 | 0 | 0 | 0.126083667 |
| baseline-shim-after | 1267 | 736 | 288 | 2 | 0.638829583 |
| developer-dir-shim | 1272 | 781 | 288 | 2 | 0.915175417 |
| developer-dir-direct | 1278 | 829 | 0 | 0 | 0.125173416 |

Each case exits 0 within its original 30-second subject budget. Original raw stdout/stderr equal the retained text files and their embedded JSON representations exactly in this run. Each JSON payload PID equals its acquisition launch PID; parent PID 1219 appears as the same observer in its original terminal census. Each case contributes its own exact PID/nonce readiness suffix, and the six selector/subject suffixes exactly reconstruct the retained common ready file. No prior readiness row is accepted for a later launch.

The three baseline environments are identical, all with PATH `/usr/bin:/bin` and DEVELOPER_DIR absent. The separate two-case override pair has identical environments and changes only DEVELOPER_DIR to the selected developer directory. The three shim stderr captures each contain exactly two `couldn't create cache file` diagnostics for `xcrun_db-*` under the host `/var/folders/.../T/` path, with `Operation not permitted`. These are captured reports of cache-creation attempts denied by policy; they do not demonstrate successful file creation. Both physical-interpreter captures have exactly zero stderr bytes. The baseline shim-after case reproduces the denied diagnostics after the physical case; setting DEVELOPER_DIR also leaves the shim diagnostics present.

Contained `/usr/bin/xcode-select --print-path` runs as PID 1238 under the same policy and baseline environment. Its original stdout is exactly 48 bytes: `/Applications/Xcode_16.4.app/Contents/Developer` plus newline; stderr is empty; return code 0; first terminal observation 0.041193083 s of 30 s; no cleanup or residual owned group. Its subject snapshots are equal. The probe reads fixed candidate files under that directory, checks recorded Mach-O/executable/containment conditions, and resolves the physical image without an explicit `xcrun` lookup or Python-shim discovery invocation. This artifact tests xcode-select only with DEVELOPER_DIR absent; it does not itself prove selector semantics under a user-supplied override.

### Original stream digests

| Case | stdout SHA-256 | stderr SHA-256 |
|---|---|---|
| baseline-shim-before | `decb33570a385f6e1d75bc3c88fb93721b5fd9a36d7912e884e36a1228a26203` | `c434da848b7cb1b6cb170854a9dae2fe775a08fb57f84664b8e06f4fc42f1561` |
| baseline-direct | `c70abd95e0869d17ee93d0d61ab39ed896d9638f6d5578a06d5dd553494fefdb` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| baseline-shim-after | `cca5b20c7c3cee7a5b89f5a07b04e8b01c301187a5a507e89075b6dc52577082` | `0cd9128003e59e1bd30bb9d2a852be3fb85d0ff3349c527fae7b1955feecc04d` |
| developer-dir-shim | `e33a89d834589ab657222e2ae7bca0f7a86359a168d7ed97e4fbcbc83bc8c3d9` | `b564abbeac5d8fda3387c5aace8a51f2c6ea6049b1b21488a2eba69731c91a00` |
| developer-dir-direct | `01f62570cb9ed1cb5b69c77ee58b8e92ce40c80bc530747421b630d0ac61f40d` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Containment, snapshots, PTY, and acquisition lifecycle

All eleven archived sandbox profiles are identical to the frozen policy: deny network operations and file writes, allow file writes only within the owned fixture plus the original null/TTY device exceptions, and deny execution of the specified browser/clipboard/AppleScript commands. There is no profile relaxation, cache exemption, PATH mask, cache clearing, or cache redirection in this probe. Fixture setup, readiness writes, raw captures, snapshots, host acquisition, and log readback are observer/control effects explicitly outside the product-row claim.

The kernel control’s original JSON identifies PID 1223, an allowed control write inside the fixture, two denied outside writes with errno 1, and TCP/UDP attempts denied with errno 1. The preserved outside sentinel has the expected original bytes, and the attempted new file is absent. Original native-log stdout retains 26,326 bytes; one exact PID-1223 network-denial match agrees with the derived readback. Both retained decoded streams are complete and their hashes agree with the corresponding raw observer streams for this run. The native-log acquisition is an observer host-control operation and a targeted denial readback, not a global transport ledger.

The command-interception control retains its mkdir-denial event and stderr, an unchanged subject snapshot, and no denied directory. Missing and wrong readiness controls exit normally but are correctly classified BOOTSTRAP_BLOCKED from their original absent/mismatched marker evidence. The PTY control retains the original `native terminal control\r\n` sentinel. Child PID 1229 naturally exits 0 and is reaped, the master closes, ownership is retained, no cleanup signal is sent, and its recorded internal elapsed time is 0.021453250 s. The outer acquisition sees terminal status at 0.169299834 s, and the original census contains neither the PTY child nor the outer owned group.

Nine before/after snapshot pairs are equal. Independently comparing them to original TAR names, types, modes, and file hashes finds no mismatch; the selector and five Python cases each contain the same 21 subject entries. These snapshots cover names, modes, contents, and links inside the fixture. They do not capture filesystem timestamps, attempted writes that policy denied, or global host state.

| Acquisition | PID | Budget (s) | First terminal observation (s) | Capture/cleanup/residue |
|---|---:|---:|---:|---|
| Bash version | 1220 | 10 | 0.050541084 | Complete; no cleanup; empty original owned-group census |
| Kernel control | 1223 | 30 | 0.096300833 | Complete; no cleanup; empty original owned-group census |
| Native log | 1225 | 8 | 1.379365291 | Complete; no cleanup; empty original owned-group census |
| PTY control | 1228 | 30 | 0.169299834 | Complete; no cleanup; empty original owned-group census |
| Command denial | 1231 | 30 | 0.074462208 | Complete; no cleanup; empty original owned-group census |
| Missing readiness | 1233 | 30 | 0.073248458 | Complete; no cleanup; empty original owned-group census |
| Wrong readiness | 1235 | 30 | 0.027562833 | Complete; no cleanup; empty original owned-group census |
| xcode-select | 1238 | 30 | 0.041193083 | Complete; no cleanup; empty original owned-group census |
| baseline-shim-before | 1240 | 30 | 0.935003334 | Complete; no cleanup; empty original owned-group census |
| baseline-direct | 1265 | 30 | 0.126083667 | Complete; no cleanup; empty original owned-group census |
| baseline-shim-after | 1267 | 30 | 0.638829583 | Complete; no cleanup; empty original owned-group census |
| developer-dir-shim | 1272 | 30 | 0.915175417 | Complete; no cleanup; empty original owned-group census |
| developer-dir-direct | 1278 | 30 | 0.125173416 | Complete; no cleanup; empty original owned-group census |

Every one of the 13 acquisition records matches its original per-run result; command, environment, and budget match the prelaunch plan; raw stream hashes and sizes match; terminal timing is nonnegative and within budget; return code is 0; no error or cleanup is recorded. Independent parsing of every original census confirms the launched PID and its process group are absent. This supports OBSERVED_GROUP_ABSENT capture finality within the instrument’s stated scope. A final group census is not a complete historical process-tree trace and cannot exclude an arbitrary descendant that deliberately escaped that group. No cleanup path was exercised by these native subjects, so this receipt gives no new native credit to fallback cleanup code.

## Product implication and remaining gaps

Read-only inspection of the published `install.sh` finds that Firefox metadata parsing is the Python execution reached in preview; the other Python sites are behind normal-mode guards. This receipt supports a bounded product candidate that selects a physical Apple interpreter for that preview parser when command discovery selects `/usr/bin/python3`, while preserving Linux, non-shim, and normal-mode behavior. It does not qualify that unexecuted candidate. A candidate must retain the unknown/no-parser fallback when selection is absent or ambiguous, preserve parser input/protocol semantics, and receive fresh native installer qualification under the unchanged containment policy.

The frozen fixture’s `[()` function refuses `-x` for every `/Applications/*` path. That is an existing fixture interception, not evidence that the observed physical Python lacks execute permission. A real Bash `[[ -x ... ]]` test bypasses that function; any narrowing of fixture interception should be reviewed as a separate instrumentation change. The source-free probe used Python’s `os.access` for this check. The artifact does not establish a general solution based on DEVELOPER_DIR, hardcoded Xcode versions, PATH changes, cache exemptions, or relaxed host policy.

For every selector/Python case, `transportAttempts` is JSON null. It means unavailable complete native attempt telemetry; it must not be normalized to zero. Empty command-event lists and equal snapshots cannot erase the shim’s observed denied cache attempts. Empty direct stderr supports the controlled launcher differential, not a claim that the physical interpreter made no filesystem or transport syscalls. Native product rows executed remain exactly 0, installer source read by the probe remains false, and nativeQualification is NOT_SUPPLIED. No whole R0016 acceptance row, final integration, merge, release, or closure is established.

## Reproducible receiving outputs

The independent verifier completed **167/167 checks with 0 mismatches**. Checks are consistency/receipt checks, not added product tests or acceptance rows.

- `/tmp/r0016-third-20261111/work/mac_native_receiving/verify_receipt.py` — SHA256 `a676897f5d5017a28f671ed85f517014d5f539411ac5c461547913efd06258c1`
- `/tmp/r0016-third-20261111/work/mac_native_receiving/checks.json` — SHA256 `79ad04c18f172e5a9b204ad67aef64d0111ea463065a45fd426a2d09afec0c8e`
- `/tmp/r0016-third-20261111/work/mac_native_receiving/zip_receipt.json` — SHA256 `a559bf957b00449ed3dc1d0916f65e7e404a0fdc16e152ed6d17978d8377713a`
- `/tmp/r0016-third-20261111/work/mac_native_receiving/tar_receipt.json` — SHA256 `c64a6cb2136800ee51b1922dfda743491a03848ce687e56d42738f87bbb89593`
- `/tmp/r0016-third-20261111/work/mac_native_receiving/source_receipt.json` — SHA256 `1b9dc72fa9d032ef5c8ea8125b3216c2893ac2e4169bed69b45adcd6f285b5f4`

Original retained API-body hashes:

- `/tmp/r0016-third-20261111/evidence/mac-probe-run-api.json` — SHA256 `f4c70b31a818b760971e398ae9a3964bf4a6248a441f9cc1fb23ce7247145d2d`
- `/tmp/r0016-third-20261111/evidence/mac-probe-artifacts-api.json` — SHA256 `4e1187aaf65fcaf94c3ffaa9a8592061be5fe31707c5f8e45908d5ad01249f09`

All evidence citations above refer to the original extracted files rooted at `/tmp/r0016-third-20261111/work/mac_native_receiving/tar_regular/installer-python-evidence`; exact per-case filenames are `fixture/python-pair/<case>/{stdout.txt,stderr.txt,readiness-window.raw,snapshot-before.json,snapshot-after.json,result.json}`, and each original terminal census/capture is in `fixture/observer-runs/001` through `013`. The original ZIP remains unmodified.
