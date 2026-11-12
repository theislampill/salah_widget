# First native full-entry failure: independent original-artifact receipt

**ORIGINAL_NATIVE_ACQUISITION_FAILURE_CONFIRMED_BEFORE_PRODUCT_LAUNCH.** Both host originals from run `43163244499` fail the first `github` fixture during clone preparation. Neither recorded composition reaches a direct installer child or held installer child. Auxiliary version, ACL-setup, and host-only baseline processes did run.

## Original custody and exact source

| Host / artifact | ZIP bytes | ZIP SHA-256 | Verified tar contents |
|---|---:|---|---|
| PS5.1 / `13918832504` | 167792 | `f532bd751852903658b717d3204eee0d5871ac253e7a7a0fee4344cdd9b03d53` | 158 members; 72 files; 908748 bytes |
| PS7.6.6 / `13918453742` | 273952 | `36ac78701c0b84bbea9a42bc712fbb85ac8b3cef0bd847d96c681900263090ff` | 167 members; 74 files; 1235600 bytes |

The nested tar bytes match each retained `original.tar.gz`. All members are unique ordinary directories/files with safe relative names; every regular file matches the extracted bytes and supplied inventory, with no extra extracted files. All fourteen archived source copies per host match committed `3f900a17121617eb6b8f0504ad958989ea8a9d39`, tree `6242ecc6bfe42e28aaf8d3469735fa926031896a`.

The retained native version streams identify `5.1.20348.5773 / Desktop` and `7.6.6 / Core`, both Win32NT and 64-bit, with host paths matching plan, route, and result envelope. The plan contains executable facts; executable binaries themselves are not archived. Original process/stream facts and report-envelope hashes were independently joined to the received files.

## Same first failure on both hosts

Each product composition report contains one `github` row, `pass_=false`, classification `FIXTURE_ACQUISITION_FAILED`, with:

```text
Prepared directory restoration failed:
Prepared clone differs beyond directory mtime:
profile/existing-profile-sentinel.bin:security
```

The generic outer rejection is the subsequent integer-one process exit. Both native process receipts explicitly record `timedOut=false`, `exitObserved=true`, and closed Job Objects. PS5.1 elapsed 56.672 seconds; PS7 elapsed 2.328 seconds. The PS5.1 duration is not a timeout finding.

The directory-preparation journals have `complete=false`, empty `plan`, empty `operations`, and the same security assertion. Direct before/prepared/after inventories are identical. Held before/after inventories are identical. Every inventory retains two equal passes and the complete row set.

## Exact ACL diagnosis

The prepared legs have the same names: 26 rows on PS5.1, 29 on PS7. On each host, **fourteen rows differ in `security`**, and there are **zero directory-mtime differences**. No other compared non-clone-identity field differs.

The fourteen rows are the profile sentinel, `subject/local`, its four Chrome descendants, `subject/pf`, `subject/pf86`, `subject/roam`, its four Firefox directory descendants, and `extensions.json`. The complete original direct and held rows—including every metadata field—are preserved in `receiving.json`. The sentinel bytes remain exactly 33 bytes with SHA-256 `91ab4beda0b1bf9b9a58eec019264e34b78d2c9528eb24151046118f90bad717` on both legs.

The sentinel's owner/group prefix is identical. Its direct DACL suffix is:

```text
D:AI(A;;FA;;;SY)(A;;FA;;;BA)(A;;FA;;;LA)(A;ID;FA;;;LA)
```

The held suffix is:

```text
D:AI(A;ID;FA;;;LA)
```

Already protected role roots—including profile, subject, and subject/temp—have matching security strings. This is a preparation security mismatch, before any directory timestamp restoration or product invocation.

## Why no installer child launched

In the exact archived `_case_impl`, `prepare_pair` precedes writing direct launch facts and the direct installer `Popen`. In the exact archived `prepare_pair`, the failing `finish_prepared_clone` precedes construction of the held driver, spec, and association. Both complete archives lack direct-launch facts, the direct entry window, held driver/spec/association, and held result/process files.

The separate `host-only-control/host-only.ps1` did run and exited zero: PS5.1 PID 6744; PS7 PID 6624. Its command and original receipt distinguish it from the installer. This is a claim about the recorded composition path, not new global process telemetry.

## Setup-order hypothesis and proposed discriminator

The source creates direct role children and the sentinel before applying parent protection. The held path first creates/protects the required parent directories and then creates copied descendants. The observed fourteen unequal security strings are confined to that asymmetric creation history. The original artifacts do not include each descendant's security immediately before and after the direct protection call, so the precise transition of every ACL entry remains an inference.

Root's proposed correction is appropriately narrow: create only the required parent paths, apply the unchanged protection to those paths, then create `local`, `roam`, `pf`, `pf86`, and the sentinel at unchanged paths/bytes before the host-only baseline. All original metadata comparisons and clone identity mapping remain mandatory. No ACL normalization or field removal is justified.

The static prefix witness should show required parents present and the other role children/sentinel absent at the protection call. Replaying the original fourteen mismatches must still reject. These checks establish order and preserved refusal, not the native fix.

The minimal native discriminator is already available in the next prepared pair: full inventories must show all fourteen original security relations equal, and the unchanged complete mapping/restoration receiver must admit before either installer leg begins. Any remaining mismatch is evidence against the proposed correction; it must remain visible. **No corrected Windows run has been received in this report, and no fix or product qualification is claimed.**

## Scope and immutable output

This lane received files as data, inspected exact source as text/AST, and wrote only this new report subdirectory. It authored no product code, executed no candidate/native program, and changed no source or remote state. The earlier static report remains byte-identical at SHA-256 `97e1f4ce7458a7fad7bf24e0a814b1a6f359d02137980ae81fb6ec6a7569f072`. Root retains correction, native receiving, and acceptance authority.
