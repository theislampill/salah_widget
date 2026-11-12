# PS5.1 native file identity correction — NEW bounded proposal

## Result and authority

The proposed diagnostic changes one receiver function, `record_probe_file_binding`, to bind a reported native module/assembly path through actual canonical resolution and a stable physical file identity. It preserves both raw spellings, original file facts, differences, and every existing lifecycle inventory. Seventeen owned filesystem/inert controls pass. This is an author result awaiting independent root review and native execution; it grants no installer or full-entry qualification.

Root confirmed entry continuity G000E at `c5cfa71f03a510cd827faa28f419a2f3445b0611`, then current continuity G000F at `8a81fb0f8504026ecfe7b39da9b44e1308a437cf`, unchanged source `cda4c6b29e8f9f2d202c0c4469a8712a74725228`, and scratch-only authority. No shared file, Git reference, installer, host policy, PowerShell process, native workflow or external publication was changed by this lane.

## Exact observed failure

Original run **43150783894 remains PS5.1 FAIL**. The authoritative received ZIP remains at `/tmp/r0016-third-20261111/work/root-windows-prepared-native/ps51/original.zip`, **187054 bytes**, SHA256 `5c2c2a5af6ac2d14fa4a8a10187b19977e7be1b51dd8730730e63e574a9c1cf4`. It was reused locally, not downloaded again. Its complete original extracted tree, including every raw lifecycle snapshot, remains under that lane's `received/installer-evidence` directory.

Exact original bytes copied into this packet are the direct pre-discovery file-binding journal, actual child input proof, inner diagnostic report, and outer route result. The journal shows:

- Test-Path/module: complete child and parent facts equal.
- Test-Path/assembly: child spelling contains `C:\Windows\Microsoft.Net\assembly\GAC_MSIL\...`; the fresh parent fact contains `C:\Windows\Microsoft.NET\assembly\GAC_MSIL\...`.
- The assembly length is **586752** on both sides. Both SHA256 values are `da18597950c115efe569dcd8f7e379704a5ee002a1f0a10421ba269deb360183`.
- `differingFields` is exactly `["path"]`; `matches` is false and the original error remains recorded.

This independently checked local evidence establishes the spelling-only fact mismatch. The original record did not capture device/inode identity; this proposal does not retroactively manufacture that observation or turn the failed run into PASS. Root reported the original PS7 source-free run successful; this lane does not borrow that native result for these new diagnostic bytes.

## Bounded correction

The child fact must have exactly `path`, `bytes`, and `sha256`, with a string path, a nonnegative integer length (excluding booleans), and a 64-character lowercase hex digest. The existing `c.fact` implementation is unchanged.

Before the first parent read, the receiver checks the absolute child path and its ancestors for symlinks/reparse points, requires an identifiable regular file, and records its device/inode and associated stable metadata. It then retains the original parent fact and the complete raw child-versus-parent difference exactly as before.

The receiver resolves both the child path and the parent canonical path on the actual filesystem. Both resolved strings must exactly equal the recorded canonical parent path. It obtains file identities before and after two fresh fact readbacks. All four identity observations must have the same device/inode, a nonzero inode, and unchanged recorded metadata. Both fresh readbacks must exactly equal the parent fact; the reported child length and hash must also match. Only the conjunction of resolution, identity, stability, and content checks sets `matches=true`.

There is no case folding, lowercase path substitution, arbitrary alias table or content-only equivalence. Distinct canonical hardlink names are refused even though they share an inode. The raw child spelling remains in `childFact`; `parentFact`, `differingFields` and `differences` remain present even for an admitted spelling difference. The added `nativeFileIdentity` object retains the resolution, physical observations and readback facts. Failed checks still append and save their journal row before raising.

The complete inventory schemas, comparisons, child probe, native host binding, constructor, preparation repair, two readiness/invocation gates, timeout/cleanup checks, ten-case semantics, guard controls, exact source bodies, and unfiltered held-before/after equality remain unchanged. The physical identity observations are additional evidence, not a replacement or projection of a lifecycle snapshot.

## Verification and useful adverse evidence

The local test loads only the named receiver function and four fact/save functions through an AST allowlist. It never imports or executes an archived controller, PowerShell module or installer. All filesystem effects are confined to this lane's owned validation fixtures.

The same test ran against the unchanged published baseline and the proposal. The baseline's final run exited 1 with three intentional discriminators: rejection of a real same-file resolution spelling, acceptance of stale content after the first parent read, and acceptance of replacement by a new inode with identical bytes. The proposal's final run exited 0: **17/17 checks passed**.

The checks cover exact-path healthy binding; real `sub/../file` resolution to the same inode; incorrect length or digest; extra/missing fields; boolean length; relative or non-string paths; malformed hash type; identical bytes in different files; `Microsoft.Net` and `Microsoft.NET` as distinct case-sensitive directories/files; hardlink names; file and ancestor symlinks; a content change after the first parent fact; and an atomic same-byte replacement with a different inode. The two latter controls demonstrate that the fresh identity/content checks are operative. The case-sensitive test deliberately supplies the other file's purported parent fact through an inert fact-provider substitution; it does not change host filesystem case policy.

Every raw JSON journal and result is retained under `validation/`. Earlier 16-case baseline/candidate executions are preserved as historical author outputs; the final script and final 17-case results are the review target. Original on-disk fixture trees, including the deliberately created links, remain outside the flat frozen packet under this lane's validation directory. The frozen packet contains their exact JSON observations without following those links.

Static verification confirms the native artifact's diagnostic bytes exactly match the baseline; exactly one of eight diagnostic roles changed. AST comparison confirms **19 other functions/classes and all other top-level declarations are identical**. No helper, PowerShell fixture or workflow body changed. `validation/diagnostic.patch`, `ast-scope.json` and `static-verification.json` give the exact scope and identities.

## Candidate and remaining boundary

Baseline diagnostic: **54512 bytes**, SHA256 `901c97e9cb5f3c7df989a5b645d52d7a8a6c910b292897a2d0b68e0e35e08168`.

Proposed diagnostic: **57115 bytes**, SHA256 `08ddd40bbdafe82cdc25bb074ee2da6b9e9ef78004d744c3daf00ea8ca06cbd5`.

Seven other input files are exact baseline bytes. A separate derived outer-route draft changes only the diagnostic length/digest pin and this frozen packet's manifest pin. It is excluded from the diagnostic packet to avoid circular manifest binding; root reviews and publishes both exact files together.

The real Windows spelling/identity observations are still prospective. An unavailable/zero inode, file replacement, differing content, noncanonical identity join, or any original strict native gate failure must remain a diagnostic failure. The next bounded action is independent source review followed by the same source-free route on the two original native hosts, with full original outputs archived. No twenty-case product matrix is admitted by this proposal. Full-entry cleanup/deadline/source-input relation/normal residual-file findings remain separately pending.
