# R15-NATIVE-01 bounded lease candidate

## Observed failure and preserved RED

Both native Windows receipts at source `a2b36da7c4b07f52cb22cff1fdeaa1e9cffd60f5f95188d8b7f65ce9fa4fa8f8` show `Directory.Move` successfully renaming a scratch root despite its held `StageNative.DirectoryLease`. Their failing row is `native directory lease prevents live root replacement`, with `observations.rename.refused = false`. The original TAR retains `attempt-renamed` directories for PS5.1 and PS7.6.6 and no original scratch pathname in those cases. This is an actual same-SID lease counterexample, not evidence of a foreign-user exploit.

The raw original receipts remain in `recovery/r0015-native-run1/Windows/receipts/`. `native-red.json` in this directory binds both receipt hashes, the original Windows TAR hash and its relevant member inventory. The prior source and native test are preserved as `source-before-a2b36d.ps1` and `native-test-before-1a8b76.ps1`.

## Reason and smallest production change

The old `OpenDirectory` access mask `0x20080` requests `READ_CONTROL | FILE_READ_ATTRIBUTES`. Its share mask3 omits `FILE_SHARE_DELETE`, but the Microsoft file-system sharing algorithm only applies this delete-sharing conflict to handles with data/execute/write/append/delete access. Metadata rights alone do not participate in that specified check. `FILE_LIST_DIRECTORY` uses bit1, the same value as directory data access. Adding that bit is the smallest access-mask change that makes this lease participate in the documented conflict check.

Only `StageNative.OpenDirectory` changes from `0x20080` to `0x20081`, with one explanatory comment. `Inspect` keeps its metadata-only access and share7. Public interfaces, ACL policy, artifact transactions, strict JSON, first-call compiler behavior, dry paths, Bash, and R0013/R0014 logic are unchanged. Exact byte comparison against the preserved old source confirms no other production changes.

This is a supported candidate remedy; actual native confirmation remains pending. A host that cannot grant the required directory-list access will fail closed at lease acquisition. The native useful initialization control and the full native suite must establish behavior on supported Windows host roots.

## Strengthened actual native discriminator

The existing live-lease row now first initializes actual staging, writes a guarded proof file, and records native identity, protected ACL and proof hash. While actual leases remain open, the same `Directory.Move` must fail specifically with Win32 sharing violation32. The original root must still have the same identity, and the destination must not exist.

The row then disposes only the lease(s) for that exact scratch root. Parent/retained leases, root identity, source path, destination and ACL remain unchanged. The same rename must now succeed, preserving native identity, ACL and proof bytes. The test restores the original pathname and reopens the actual production lease before ordinary cleanup. This positive prevents a generic ACL/fixture denial from satisfying the refusal oracle.

## Verification and freeze

- New source SHA-256: `9e8fd30cdb7c625882f4cb2cfb383328515225d0c180549f876bb7162a4d1cff`.
- Revised native test SHA-256: `d11449d18861c2be9890f226c26b116c08c7903845b102191399ddd3720a124d`.
- Source and revised test parse under actual local PowerShell7.6.6.
- Three focused actual controls pass: exact-file parser/ASCII; healthy actual download/manual Chromium caller; scratch cleanup holding ancestor leases until deletion. These use the explicit POSIX native-boundary adapter and do not establish Windows sharing semantics.
- Native PS5.1/7.6.6 remedy result: **PENDING**. No local result is substituted for it.

Source custody has been returned to root. No commit, remote, workflow, collector or unrelated source modification was made by this child. `freeze.json` and `bounded-candidate.diff` give the exact candidate packet.

## Primary references

1. [Microsoft MS-FSA, Algorithm to Check Access to an Existing File](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fsa/82b364ce-6d7b-422f-8d88-4db32eea809a), delete-sharing pseudocode, observed lines66–83.
2. [Microsoft File Access Rights Constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-access-rights-constants), FILE_LIST_DIRECTORY/FILE_READ_DATA and FILE_READ_ATTRIBUTES, observed lines61–70.
3. [Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew), share-mode semantics and attribute access exception, observed lines70–95.
