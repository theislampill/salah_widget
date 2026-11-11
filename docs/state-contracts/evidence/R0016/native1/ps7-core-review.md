# R0016 native run 1: independent PS7 core receiving

**Disposition: GAP-REVISE for native qualification.** The original failures are accurately retained. The archive and raw sidecars reconcile; neither a corrected product pass nor a mutation-discriminator pass is established.

Reviewer: `/root/g18_ps7_core`. Continuity: `G0018@24b9fa26ae7a186c735bfdc4afd1bc691bd6e778`. Review performed by regular archive-member reads, without fixture extraction, installer execution, repository edits, or remote mutations.

## Immutable inputs and receiving evidence

Candidate: `3d091c3515c6258e4983ea71d2426be399881936`; tree `2e57dcac25c52f3fd968006bfd3ddacb5d7073bb`; sole parent `bf566111fe530b5de2c7c63ca4586e83d5f4b965`.

| Input or report | SHA-256 |
|---|---|
| Original `Windows-ps7.zip` | `673ccbdac4e06162c9ebb066f01989fe23ebbbfda7f33bd13a926221f3ddb9db` |
| Original `Windows-ps7.tar.gz` | `fff2e623b7b233be237039d002e6b20a55935630e1e82a658c9d44e9a252fe47` |
| Original `ps7-install-preview.json` member | `50c88f275906477810a1406a3cdd0de3c887bab13f10f7a25f56cd25496bd740` |
| Actual `install.ps1` | `b579fb83c91c9f45b7ca461f6e7a1cafbc7af1e2132dee5b1cb333623ac2cc3e` |
| Actual core test | `1cb7eeea0f8e72ffb3ca8ef8492778dabef4d009474f26cfe5601c24f658094b` |
| Actual timing fixture | `b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1` |
| `core-receiving.json` | `ef6e4cf71788961428e465fbc51f84524a43113ea90a4709626af2b24e6fc5bc` |
| `function-source-binding.json` | `01ef4fb3111ddd5e83a4a7a510dc0a50908b422a5f896506338dd4750b286333` |

The ZIP's sole regular payload equals the retained TAR. The original core JSON equals the existing top copy. All 1,477 receiving checks pass: original identity, source binding, raw snapshots/streams/launch records, actual guard nonces, attempts, terminal observations, and unchanged input closure reads. These are receiving checks, not product qualification assertions.

The frozen installer and generated driver match current source bytes. A separate read-only comparison binds all 53 function names, their order, and every exact contiguous source extent in each of nine archived function files to its corresponding base or mutant source. It does not claim to replace PowerShell's AST parser.

## Outcomes retained

| Population | Original outcome |
|---|---|
| Four independent guard controls | 4 PASS, scoped to the intended positive/denied write and loopback attempts |
| 37 helper rows | 37 `PRODUCT_ASSERTION_FAILED` on exact subject equality |
| 14 wrapper rows | 14 `PRODUCT_ASSERTION_FAILED` on exact subject equality |
| Eight discriminator pairs | 8 failed pairs; all eight healthy members fail subject equality |
| Native positive companion | `PROVENANCE_BLOCKED`; zero native cases executed |

Thus the original top-level count remains **4 passed / 59 failed**, and **all eight discriminator pairs remain uncredited**. The 67 product subprocesses comprise 51 direct cases plus 16 healthy/mutant members. All completed with retained process, stream, snapshot and guard evidence. Five mutants independently record denied `CreateDirectory`, `Dispose`, `Set-Clipboard`, `Add-Type`, and `Connect` boundaries. Three others retain wrong-return observations: a cached path, Boolean true, and a null-plus-false result. These observations do not repair the failed matched prerequisite or establish native normal/NoOpen survival.

## Exact subject differences

Every one of the 67 product subprocesses has exactly these two changed paths:

| Subject-relative path | Changed fields | Unchanged fields |
|---|---|---|
| `/temp` | `lastWriteUtc` | name, attributes, hash, SDDL, link target |
| `/user-profile/AppData/Local/Microsoft/PowerShell/StartupProfileData-NonInteractive` | `hash`, `lastWriteUtc` | name, attributes, SDDL, link target |

There are no added or removed product snapshot paths. No other retained file hash, attribute, ACL or link target changes. The core snapshot compares timestamps as well as names and bytes (`tests/install-preview.ps1:33–49`); its shorter error text at line 384 does not enumerate every compared field.

Concrete anchor: `ps7-install-preview.json/results[4]`, `helper-compiler-native-api-load`:

- `/temp.lastWriteUtc`: `639300034266284424` → `639300034277232613`.
- Startup profile hash: `7cd88f1be58279f50f7c64961bf641765f8da056abc7ca3facdbc2e9b1a359cf` → `7c9287004c48a312cd47aa3b85cd55de0095ac8a12bd203562d991c83f71c627`.
- Startup profile `lastWriteUtc`: `639300034274736767` → `639300034286466190`.
- Final startup-profile bytes: 82,008; their original TAR member hashes to the reported after digest.

Original raw members are under `installer-evidence/ps7-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/`. The complete report records exact deltas and raw-member hashes for all cases.

## Host evidence, timing and unresolved cause

All 67 no-installer baselines create the startup profile file and its parent directories. All four no-installer guard controls do so as well. Separate original `ps7-install-host-bootstrap.json` rows show both cold creation and **warm rewriting** in each of two no-installer variants. A prior host launch does not make subsequent startup-profile bytes stable.

The configured module-analysis-cache file is absent before and after every product process. It must not be conflated with the separately observed startup-profile file.

Across all 67 product launches, the TEMP directory's recorded last-write time is 89.8512–179.4409 ms after launch start, 625.1454–1128.8675 ms before retained core guard-readiness mtime, and 281.2373–736.005 ms before the final source-event-file mtime. The startup profile's last write follows guard-readiness mtime by 78.0935–782.6996 ms. These are filesystem timestamp comparisons, not a syscall trace.

No transient TEMP filename or operation survives in the core before/after snapshots. A startup policy probe is therefore **unproved as the specific TEMP cause**. Source preparation and independent host activity must be distinguished with a native operation/phase trace before changing the fixture's measurement boundary. Matching aggregate patterns are not a safe basis for a path exemption.

Every baseline-after → product-before transition also changes the `Microsoft/PowerShell` directory timestamp, with no name, byte, ACL or attribute change. This extra inter-process metadata transition is preserved in the report.

Two evidence limitations matter:

- The generic timing fixture watches `ready.txt`, while the core validates `preview-ready` against a separate nonce. All actual core nonces reconcile; generic `readiness=false` and null timing fields do not mean the core guard was absent.
- The producer deletes/reuses its host-baseline terminal JSON and nonce file before the product run (`tests/install-preview.ps1:319–339`). Baseline snapshots, launches and streams remain, but that earlier typed terminal result cannot be independently reread from the archive. Likewise, overwritten baseline startup-profile bytes survive as digests, not complete byte copies.

No exclusions, whitelist, weakened assertions, source correction, or retrospective pass is proposed or applied here. Full-File coverage and whole-46 adjudication remain with their separately assigned reviewers.
