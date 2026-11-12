# Combined Linux original receiving and bounded carrier repin review

## Disposition

**PASS for the exact one-digest repin as the carrier for the next original 45-case native acquisition.** The received run remains **FAIL: 37/45 preview rows passed, eight failed**. This review supplies no native pass, acceptance, readiness, or closure claim. The independent data-only verifier completed with exit 0 and **58/58 checks passing**; its results, original archives, inventories, source copies, API metadata, and actual execution receipt are retained in this packet.

The reviewed candidate is `installer_preview_linux_normal_ownership.py`, 68,793 bytes, SHA-256 `6ec0e06f3cc76f578cc9dca5e2e62661deb180819d24e974cb68f69e56ba95b3`. Reversing its sole digest-literal substitution reproduces the historical carrier exactly: SHA-256 `2b4b76dd792505566405abf65fe5c816507e10820b4dda5136aae80b99e705bd`. No additional containment implementation is needed for this acquisition path.

## Original identity and custody

| Item | Exact identity |
|---|---|
| Native run / artifact | `43171927513` / `13921719935` |
| Commit | `a4c617ebeedfb507c0cb7a472683cce47ad62522` |
| Tree | `7f7aca595593db5014dd0932476c35a85eb8ba0c` |
| Original ZIP | 1,110,819 bytes; SHA-256 `e88a4742b64926571c9fc20977eef28e5eaf67caf4370046b586a21e2095548e` |
| Original nested TAR | 1,221,311 bytes; SHA-256 `0595de2566e9fcbe79a75be6168565f2b82a3ddf03f469d188184f406aa6a4c8` |
| Combined `install.sh` | 46,460 bytes; SHA-256 `27442c0e6a6dbd6390ba1ea9b8b3efa2bfb2a910037e2c415756f9169a5c7b3f` |
| Previous pinned `install.sh` | 44,673 bytes; SHA-256 `d19ed5d90e1faf0d9ac66415814a3a68e28c6ae61730acd4eaef1b9588830cc5` |

The ZIP CRC, its single TAR member, all 2,976 unique TAR member names, all 1,366 regular-file digests (4,938,132 bytes), and seven retained symbolic-link metadata rows were independently checked against the supplied extraction. Links were neither followed nor recreated. Canonical POSIX paths, uniqueness, and absence of link ancestors were checked; deliberate literal backslashes in fixture filenames remain ordinary POSIX filename characters. All 50 declared original source hashes match immutable Git objects at the recorded commit, and the archived preview source is byte-identical to that commit's `install.sh`.

API metadata binds the artifact size, digest, and head commit. Job `131027044637` completed with failure in the native-matrix step; archive and upload steps succeeded. The original preview command has exit 1, with recorded start `2026-11-12T06:59:47.113691+00:00` and finish `2026-11-12T06:59:54.057374+00:00`. No duration-based timeout inference is made. The three original preview-report copies agree byte-for-byte and preview stderr is empty.

## Preserved failure and narrow attribution

The first ten command suites passed: Bash, Bash entry, discovery, detectors, discovery mutations, original mutations, builder, native staging, staging-parent, and Linux-owner. The staging-parent suite contains 20 passing controls against the combined source. The subsequent preview report retains its original classification: 37 `PASS`, eight `PRODUCT_ASSERTION_FAILED`, zero `BOOTSTRAP_BLOCKED`.

The eight failures are the normal caller, NoOpen normal caller, and six mutation pairs: eager initialization, preview cleanup, cached path return, suppressed copy success, clipboard attempt during preview, and swallowed direct transport. Each actual normal companion reaches selection of two eligible targets, then exits 1 with no recorded effects and `Untrusted ancestor owner: /`. The six mutation functions run their negative oracle before their required normal companion; these pair failures do not supply successful mutation-pair qualification. Independently reconstructing each mutation through AST literal data reproduces its exact archived bytes.

`installer_native.py` invokes `tests/install-preview.py install.sh` directly. That fixture uses a one-ID user namespace and a read-only bind of the host root as `/`; it does not invoke the existing ownership-repaired carrier. This source route and the repeated terminal refusal support a harness/root-ownership attribution. The following measured boundaries remain distinct:

| Evidence | What the original establishes |
|---|---|
| Host acquisition | UID/GID 1001 before the sandbox. |
| Eight preview normal acquisitions | UID/GID 0; groups `[65534,65534,65534,65534,0]`; private HOME/TMP/fixture directories owned by UID/GID 0, mode 0700, with physical path equal to spelling and no symlink. |
| Preview child root and privileges | No child `/` stat, child UID map, or child capability-set measurement is retained. The numeric guest-root owner and actual preview child capability sets are unestablished. |
| Separate passing Linux-owner suite | Host `/` is UID/GID 0, mode 0755. Its distinct subject runs as UID/GID 1000 with no groups, zero permitted/effective capabilities, and NoNewPrivs 0. These observations belong to that separate suite. |
| Preview containment bootstrap | An inside write succeeds; two outside writes are refused with EROFS; TCP and UDP are refused with EPERM; command and readiness negative controls are detected. These checks do not fill the absent child-root/capability observations. |

An unmapped host-root owner is an inference from the launch route and observed refusal, not an asserted numeric observation from this run. The original errors and classifications are preserved unchanged.

## Exact repin compatibility

The candidate changes only the `INPUTS` digest for `install.sh`, from `d19ed5d9…` to `27442c0e…`. Every other byte and AST node is unchanged. Python syntax is valid. The original 45 rows, 61 phases, six mutation mechanisms, six expected syscalls, eight actual normal invocations, lifecycle checks, denial behavior, strict comparisons, adverse-result retention, and capability/NoNewPrivs checks are unchanged.

The existing owned-scaffold path creates private caller-owned ancestors and binds that scaffold read-only as `/`, binds system/input/outside paths read-only, permits only the fixture write area, and uses private network/PID namespaces. Its existing bootstrap drops all five capability sets including the bounding set and verifies the required identity, namespace, capability, and NoNewPrivs observations. These are preserved implementation requirements; they are not claims that the new combined source has already passed a native execution.

The combined Bash source adds supplied-spelling/symlink checks and resolves the physical parent before its original ancestor scan; it also corrects the macOS permission-mode reading. The Linux stat branch and the entire prior ancestor/terminal owner-and-mode predicates remain byte-identical. Canonical, non-symlink, privately owned scaffold ancestors are compatible with the added checks. No production owner predicate or filesystem/network protection is weakened by the repin. `--run-full-fixture` skips the separate interpreter-control loop, so that loop's older trusted-parent model does not obstruct this mode.

Retained historical source/phase/product receiving reports describe the earlier 45-row/61-phase success and bind the same carrier and fixture bytes. They are ancillary evidence here: their original archives and extracted historical payloads were not available in this receiving folder and were not newly received by this review. The exact carrier-byte comparison is independently established from the retained source and immutable repository objects.

## Next acquisition and limits

The bounded next action is the parent's existing `--run-full-fixture` qualification using the exact reviewed repin and combined `install.sh`. Its unchanged original phase, source, containment, zero-capability, NoNewPrivs, cleanup, normal-companion, and negative-control requirements must remain effective. A new failure must retain its original result and raw observations. A source review or historical result cannot substitute for that new native result.

This receiver performed archive/data inspection, immutable Git reads, AST/literal analysis, and pure receiver checks only. It did not run the installer, native carrier, archived code, or a contained child; change shared sources; or publish anything. `execution.json` records the actual verifier result and three corrected receiver-scaffolding mistakes without changing the original or candidate evidence. `receiving-results.json` contains the detailed checks and original findings; `archive-inventory.json`, `retained-link-metadata.json`, `metadata/`, `source/`, and the complete original ZIP/TAR provide the supporting custody record. Parent admission and lifecycle decisions remain separate.
