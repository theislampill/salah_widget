# Windows C3 prepared-directory metadata — bounded repair proposal

## Disposition: NEW preparation-only proposal; native result remains unqualified

The original C3 run **43148231568** failed before any diagnostic PowerShell child started. Both complete 24-row prepared inventories are stable across their two passes. PS5.1 has **two** protected directory-mtime differences; PS7.6.6 has **five**. Every other protected field agrees. The strict comparator correctly refused them.

The proposed correction changes only source-free clone preparation in `tests/install-entry-driver-diagnostic.py`: **54,512 bytes**, SHA256 **`901c97e9cb5f3c7df989a5b645d52d7a8a6c910b292897a2d0b68e0e35e08168`**. All seven other native diagnostic inputs remain exact C3 bytes. The existing complete metadata comparator, both readiness gates, native file-fact equality, held full-before/full-after equality, control semantics, budgets and original normal/NoOpen behavior are unchanged.

This proposal passed **14 owned/inert checks**. It has not run on Windows. It does not advance the earlier PS5.1 native-file mismatch or establish the repaired PS7 Utility readiness, because neither was reached by C3. No installer, PowerShell, native job, shared source, branch, policy or external publication was executed or changed here. Root remains the sole shared writer and publisher.

## Exact original evidence and receiving boundary

The independent receiving lane supplied the original artifact files under `/tmp/r0016-third-20261111/work/mac_native_receiving/entry-driver-c3-native-receiving`. This lane reused those local originals without downloading them again.

| Host | Original ZIP | Bytes | SHA256 |
|---|---|---:|---|
| PS5.1 | `r0016-entry-driver-Windows-ps51-43148231568-1.zip` | 158,592 | `287c208f353d23a445be993104b25df8548656d87a3d8e0a5253e8119beaa6ef` |
| PS7.6.6 | `r0016-entry-driver-Windows-ps766-43148231568-1.zip` | 176,011 | `c4eb3fc6c506f1e901b4ae56633ed7032ab9c6a393bd578ae4d828714be783e4` |

The source actually copied into both native fixtures is the original 49,138-byte diagnostic, SHA256 `c5f0d9cf62f4557ef8f838a08dc4c402f791076842b0c69e84bfb773020e458c`. The outer plan identifies `C:\hostedtoolcache\windows\Python\3.12.10\x64\python.exe`, 104,952 bytes, SHA256 `4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a`. That is the original provider association; it is not a claim that this local POSIX test executed that binary.

This packet retains exact full driver reports, outer plans/process/capture files, and all four original prepared-inventory files under `original/`. Per-host `full-protected-differences.json` independently enumerates every protected mismatch from all 24 rows, retaining each complete direct and held row. The original source identities are recorded separately. Both original `driver-diagnostic.json` files remain FAIL with `directNeutral: null`, one failing fallthrough-preparation result, and no association receipt.

## Complete protected differences

| Host | Role / relative directory | Direct mtimeNs | Held mtimeNs |
|---|---|---:|---:|
| PS5.1 | profile / `.` | 1794454009174039000 | 1794454009158406500 |
| PS5.1 | subject / `roam/Mozilla/Firefox/Profiles/fixture profile` | 1794454009174039000 | 1794454009158406500 |
| PS7.6.6 | modules / `.` | 1794454007355630600 | 1794454007339993900 |
| PS7.6.6 | profile / `.` | 1794454007355630600 | 1794454007339993900 |
| PS7.6.6 | subject / `local/Google/Chrome/User Data` | 1794454007324377600 | 1794454007308749100 |
| PS7.6.6 | subject / `roam/Mozilla/Firefox/Profiles` | 1794454007339993900 | 1794454007324377600 |
| PS7.6.6 | subject / `roam/Mozilla/Firefox/Profiles/fixture profile` | 1794454007355630600 | 1794454007339993900 |

These are integer values without rounding, case folding or tolerance. `prospective-original-metadata-plan.json` maps the seven observed rows to their exact held paths and requested source mtimes. Its status explicitly says **PROSPECTIVE ONLY**; it is not an altered native result or an actual applied Windows repair.

## Cause established, and the observation limit

The demonstrated failure is preparation fidelity: the two finalized fixture copies do not have equal protected directory timestamps before any diagnostic child can run. The original `make_pair` writes all direct-role contents before `shutil.copytree`. Subsequent held driver/spec creation is under `control/`, outside the compared six input roles. No source-free native body, host startup, readiness probe or installer can explain these particular C3 mismatches because none started.

The original receipts do **not** include a source inventory immediately before copying or a per-directory copy-operation trace. They cannot distinguish a source timestamp that became visible later from a directory timestamp not faithfully preserved during copying. No NTFS implementation mechanism is asserted.

The exact-tag CPython 3.12.10 source was inspected through a read-only GitHub fetch. Its `copytree` can pass directory-entry objects into recursive copying; `copystat` obtains metadata from those entries, and the Windows path may suppress an OSError from final directory metadata copying. These are relevant library behaviors, **not proof that a particular one caused this native run**. The new preparation records remove the missing before-copy observation and explicitly verify the resulting physical metadata. The received source excerpts and URLs are retained in `provider-source-excerpts.json`, without claiming those excerpts are a native trace.

## Minimal construction repair

The proposal adds one helper, `finish_prepared_clone`, and changes only `make_pair` among existing functions. A `stat` import supports directory-type checks.

1. After every direct input has been written and before cloning, capture the complete two-pass direct inventory as `direct-before-clone.json`.
2. Complete the existing clone and all held-only control/spec preparation. Capture the complete current direct inventory and require exact equality with the frozen source inventory. Capture the complete held inventory before restoration.
3. Validate the full name set and all existing protected fields. Only an explicitly observed **directory mtime** disagreement may become a preparation operation. A changed file time, file bytes, mode, attributes, security descriptor, type, name or any other protected field is refused.
4. Save the exact plan before writing. Each operation retains the complete source and held rows and exact target path. Process deeper directories first. Freshly inspect the target and its ancestry through the held root, refusing links, reparse points, non-directories and stale recorded identity/metadata.
5. Restore only that held directory's mtime using integer nanoseconds and preserve its freshly observed atime. Do not change file bytes, names, mode, security or attributes. Record the attempted operation and actual before/after stat facts.
6. Independently attempt full final inventories for **both** legs, even after a failed operation. Require the direct source still to equal the frozen input. Run the unchanged `map_inputs` comparison over all finalized rows, with **no directory-time exception**. Only a complete successful receipt permits `make_pair` to return.

The new raw files are `direct-before-clone.json`, `held-before-directory-restoration.json`, `direct-after-directory-restoration.json` and `directory-preparation.json`, alongside the existing `direct-prepared.json` and `held-prepared.json`. The compact preparation receipt binds those full files by exact file facts instead of duplicating every inventory. The association records the preparation receipt's exact file fact. All old and new observations remain under the owned output root for ordinary complete archival.

The existing `ROW_FIELDS` and `CLONE_FIELDS` are unchanged. Device/inode/ctime differences retain their pre-existing explicit clone-identity treatment. No new field is removed from equality. Subsequent held-before/held-after equality is untouched and has no preparation or cache exception.

Python 3.12's Windows `os.utime` implementation does not provide `follow_symlinks=False`; adding that keyword would create another platform refusal. The proposed call therefore uses the available integer-nanosecond API only after checking the entire owned target ancestry during private preparation, before any diagnostic process exists. Exact post-readback remains mandatory. This does not alter host policy or establish protection against an unrelated actor replacing private fixture paths concurrently.

## Actual bounded checks

`python -B test_preparation.py` completed with exit 0 and **14/14 checks** after correcting one missing `ntpath` binding in the isolated test harness. The initial harness-only failure and original harness bytes are preserved under `validation/`, with its partial owned fixtures unchanged. It supplied no candidate/native outcome.

The completed tests execute only fixed AST-selected preparation/inventory functions against owned local filesystem fixtures. They do not import the controller's runtime path or launch PowerShell, processes, sockets or installers.

- The original constructor receives explicit directory-time-loss injection of the observed kind and fails its unchanged comparator. This is the red discriminator; it is not called an NTFS reproduction.
- The proposed healthy fixture has no restoration operations and retains a complete 24-row association.
- The proposed drifted fixture restores exactly the two planned owned directory mtimes and retains complete equality afterward.
- Metadata permission failure and a deliberately rounded timestamp remain failures with raw final observations.
- Changed file mtime, changed Firefox bytes and an added profile filename are refused before restoration.
- A direct input changed after planning is refused by the frozen-source comparison.
- A stale held directory or a directory replaced by a symlink after planning is refused before `utime`; the owned outside sentinel remains unchanged.
- Both actual original Windows inventories remain rejected when replayed unchanged.
- An AST check confirms all existing driver/receiver functions except `make_pair` are unchanged, and the exact common helper/field sets remain pinned.

`test-results.json`: 10,394 bytes; SHA256 `d4ab245d20c713ccde32d99737b56643eed2629adbd2e95b1b6c3ec028a67d65`. Raw per-case preparation receipts, complete inventories and operation logs are retained in the owned test directories. These checks establish the bounded construction logic on this local filesystem. Exact Windows metadata restoration and all downstream source-free driver behavior remain unqualified.

## Publication composition and next native boundary

`proposed/tests/` contains the exact eight next-input files; `input-identities.json` records original and proposed bytes/hashes and proves that only the diagnostic Python file changed. `candidate.patch` is limited to that one file. This is NEW code with no historical/native PASS transfer.

The outer route pins the diagnostic byte length/hash and an input-manifest identity. After this input proposal is frozen, a **separate derived pin draft** changes only those two bindings in the current published outer route. Root must review both the source patch and that derived binding before publication; no shared edit or dispatch is performed here. The unchanged outer lifecycle, host environment, capture and fixed eight-role admission remain in force.

The next bounded native attempt is the same source-free diagnostic on the existing exact hosts with these reviewed input bytes. Preparation must first produce an admitted exact association. Only then can the first neutral pair test the C3 readiness and native-file observations. It may still fail honestly at those later gates. The full 20-case product composition is not admitted or executed by this proposal.

## Retained full-entry reference, without expansion

The exact 38,860-byte full-entry reference is `/tmp/r0016-third-20261111/work/root-windows-entry-route-review/direct2/frozen-driver-diagnostic-2/reference/install-entry-native-composition.py`, SHA256 `f1a98a4e2f46b379d739cb25e6f16dc655c8c2eb4f7b3a26b49abf15542410d4`. It already uses the current helper API. Today's fix is diagnostic-only; product `prepare_pair`, the unfinished source-input relation and long-path questions remain separate inspection work.

`full-entry-reference-locator.json` supplies the exact duplicate, retained DCR01 adverse and later source-free review context. The original full-entry review directory is absent from the restored workspace locations checked; the later source-free review must not be mislabeled as that original report. No full-entry file was rewritten or executed here.
