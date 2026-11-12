# Native6 Windows transaction mutation driver receiving

**Disposition: PASS_WITH_SCOPE_LIMITS.** Both native Windows hosts completed the actual unchanged-source prerequisites and all nine intended mutation/positive pairs under driver `732acd9`. The final read-only receiver passed **1,837 checks** and bound **391 native6 archive members** plus **16 selected native5 members**. This is driver-scope evidence, not whole-work-order acceptance.

## Exact packet

| Input | Identity |
|---|---|
| Native run | `43028305607` |
| Commit | `d96f87825f02077da7f6afe742d30aecfd1fc005` |
| Tree | `5911c099ad446e0f1c7a1ff66687523cc9c97044` |
| Windows ZIP | `76815f2a6a27ecaf3db65f64acc0deb844bbe391230255f2607e6c3192ce505e` |
| Windows TAR | `98484f9cb545402e272ec29b04315e15e9296bdff53b91e5544c149b6842a37d` |
| Actual production `install.ps1` | `ab2d8470367a539a9c6605717a11edc1bf019681d7ec5a65ef0a54e83a67f88e` |
| New mutation driver | `732acd9fb371926c28e2d410de2741703b1397f0eb38129384b1cd6e08ac23bc` |
| Old mutation driver | `08a1b3263f6eef4560581b0bf104ee4ef27fe0356cb9721d845740378caa567d` |
| Unchanged transaction fixture | `c6f5734352edfc8240eabc4d0009ec957c289213f7842c1acaef99dc2e4789c0` |
| Exact derived failure-control fixture | `d401982fa83e4ba5242aacdf4f4bd20b84f444eed62944032cb36d58e0f677fa` |
| Unchanged native custody fixture | `ccd63764db46c58225d3ddd95302b153337bd947e15c7eed585486088ed94eba` |
| Canonical preset | `9197c9bcfaf34ff06505963862e4e9280d3ad521e1ed287183f5d71cbce6b95f` |

The ZIP's single TAR payload matches the retained TAR byte for byte. Top copies match original archive members. Each archived base source, derived fixture, native fixture, preset and mutant is compared with the exact immutable Git source and statically derived literal mutation. No driver or product module was imported or executed during receiving.

## Actual outcomes

| Host | Prerequisites | Additional native cleanup prerequisites | Intended mutant failures with passing positives | Terminal command |
|---|---:|---:|---:|---|
| Windows PowerShell `5.1.20348.5773` | 13/13 | 2/2 | 9/9 | Exit0; 13:30:09.607512–13:30:38.833442 UTC |
| PowerShell `7.6.6` | 13/13 | 2/2 | 9/9 | Exit0; 13:32:56.171440–13:33:31.029107 UTC |

Both hosts ran without the POSIX adapter or a reduced mutant selection. All18 mutated files parse. Every actual mutation run reports exit1, its intended named target failure, and a passing positive. The16 ordinary mutation runs additionally contain a passing whole-source parser row. The native foreign-root mutation first passes its exact unchanged-source healthy/adverse pair.

| Mutation | Actual target discriminator on both hosts | Positive evidence |
|---|---|---|
| Existence-only cache | Interrupted acquisition returned a usable-looking path | Healthy actual manual caller passes; one copy |
| Direct write to ready | Changed source overwrote predecessor archive | Healthy actual manual caller passes; one copy |
| Delete before validation | Failed replacement deleted prior bundle | Healthy actual manual caller passes; one copy |
| Delete after success | Successful restaging deleted prior bundle | Healthy actual manual caller passes; one copy |
| Parse warning with ready path | Malformed preset returned a usable-looking path | Configured preset passes; target and positive each reach one copy |
| Global string replacement | Unrelated local=1/Unicode string changed | Integer-preserving positive passes and reaches one copy |
| Foreign-root cleanup | Actual replacement sentinel is absent after cleanup | Ancestor/retained-consumer positive passes, including fresh consumer exit0 |
| Dry-run pretend-ready | Warm-cache preview returned a usable-looking path | Healthy actual manual caller passes; one copy |
| Success-pipeline diagnostic | Download result is not one clean path | Configured preset positive passes; one copy |

The native foreign-root failure is attributable to the actual post-cleanup read, rather than a compiler/bootstrap exception: the unchanged fixture creates a replacement directory and sentinel, checks changed identity, invokes `Clear-OwnedScratch`, then reads the sentinel. The mutated source removes only the two custody checks. The baseline verifies that same target and positive before mutation. See immutable `tests/install-staging-windows.ps1` lines251–266 and mutation recipe lines228–233 of `tests/install-powershell-mutations.py`.

## Driver delta and retained evidence

The native5-to-native6 driver diff changes the fixture parent from the driver directory to its parent, adds `retain_child_fixture`, reports auxiliary roots, and admits each actual baseline/native/mutation fixture before giving it result credit. It does not change the source, transaction/native fixtures, mutation recipes, selected cases, capture logic, timeout, target error matching, positive assertions or kill criteria. AST equality confirms every earlier helper, both literal inventories, and `main` after removal of only those explicit retention additions. The fixture launch differs only in its parent argument. Relevant immutable driver anchors: lines294–304,319–347,383–418 and434–489.

Each host reports **11 unique Unicode child roots**, each a direct sibling of the driver root under its declared disposable parent and retaining the full32-hex UUID plus `ص`. All22 roots have exact raw receipt strings, corresponding collector entries and nonempty regular-file subtrees in the original TAR. All selected retained regular files are hashed in `bindings.json`; no archive link was traversed. The driver's live Windows lstat/reparse admission is source-bound evidence; offline review cannot re-lstat the ended VM.

All **40 child receipt sets** retain raw stdout/stderr binaries, readable derivatives and parsed JSON. Strict UTF-8 decoding and exact JSON equality are checked. Readable Windows copies preserve the actual newline expansion, including CRCRLF. PS5.1 module-preparation CLIXML is retained, framed and parsed completely; all contained records are progress with the expected module-preparation activity. No diagnostic bytes are silently discarded. Child terminal exits are recorded and gated by the immutable driver; this packet does not include a separate external process monitor for every child.

## Historical comparison and receiving limits

Native5 remains unchanged: PS5.1 passed13 prerequisites and nine mutation pairs; PS7 passed only3 of13 prerequisites and executed zero mutants. Its original failed rows and raw baseline streams are separately bound. Native6 removes one redundant38-character driver component while preserving full UUIDs and Unicode names. Its passing observations establish that the revised acquisition route works for these cases; they do not prove a single underlying cause for every earlier Inspect/create failure.

Four initial **receiver-only** failures are retained with hashes and explanations in `review.json`: the Windows readable-newline premise, an empty-stderr premise, row ordering, and concatenated CLIXML envelopes from the native consumer child. The final checks use exact observed encoding/framing and exact case membership; no product assertion was weakened or test rerun.

This report does not assess the authored compiler-security fixture, full51 denominator, other-host lifetime/export results, R0016 complete-file preview/normal/NoOpen requirements, general Windows long-path support, independent filesystem/network containment, release or owner acceptance. Those remain with their assigned reviewers and root. All receiving was read-only except this scratch report directory; no native, PowerShell, compiler, installer or test execution, archive bulk extraction, source/shared modification, or remote action occurred.
