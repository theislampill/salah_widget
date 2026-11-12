# R0015 independent Windows native2 review

Reviewer: `/root/r0013_review`. This is an attributed engineering and whole-contract review, without merge, owner-approval or lifecycle authority.

**Disposition: not engineering-ready.** The native directory lease correction and four actual normal/NoOpen consumers are qualified within their recorded scope. A demonstrated PowerShell 5.1 compiler-custody defect and the PowerShell 7 mutation prerequisite failure remain open. The collector's overall Windows `FAIL` is retained. Acquired diagnostic observations are not acceptance.

## Exact inspected inputs

| Input | Binding |
|---|---|
| Commit | `65410ae4dca07a3305e337c8215173a197abe4de` |
| Git tree | `886621be95d6789ae2b27ab5aa864a24217266d9` |
| PowerShell installer SHA256 | `9e8fd30cdb7c625882f4cb2cfb383328515225d0c180549f876bb7162a4d1cff` |
| Workflow run / artifact | `42987919795` / `13840572772` |
| Original ZIP SHA256 | `80132bbfa1b2575eaafdb663ed98a862c0fcc9056816975c55786bafea4315a5` |
| Original TAR SHA256 | `4688a280f99b2acfdfaf2e84e84247d540cdb3744824d4a2262d3798b82a85dc` |
| Detailed review JSON SHA256 | `dea8c934210818457fa27ca7107b9366ab46e063927316612e6df59a16f09fd9` |

Original ZIP and TAR are preserved in `recovery/r0015-native-run2/`. Only bounded top-level regular receipts were copied out. Independent verification reads named regular archive members, checks duplicate membership and source/test Git blobs, and does not bulk-extract fixtures or follow archived links. No native suite was rerun during receiving.

## Findings

### Critical

No Critical finding is established by the inspected evidence.

### Important — R15-NATIVE-04: compiler filesystem effects precede native custody

In the exact installer, `Initialize-Staging` invokes `Initialize-StagingNative`, which calls `Add-Type -TypeDefinition`, before `Get-TrustedStagingParent` validates the terminal staging parent. The native PS5.1 first-call probe supplies direct contrary evidence to the required before-effect custody boundary.

The fresh adverse child has no initial StageNative type, equal verified TEMP/TMP/native temporary path, an active watcher proven by create/delete control events, and a matching process ID and random nonce across readiness, launch context, boundary handoff and final receipt. Its actual first parent-check delegate is paused while the observer drains events. The exact Add-Type call returns before that boundary is released.

Before admission, the adverse child produces **32 non-control events: 9 Created, 15 Changed and 8 Deleted**. They include a compiler directory, `.tmp`, `.0.cs`, `.dll`, `.cmdline`, `.out`, `.err`, `CSC*.TMP`, and a parent-level `RES*.tmp`. After the boundary is released, the actual initializer rejects the foreign-create terminal parent. No scratch or retained root has been admitted. Later refusal and transient deletion do not undo these earlier effects.

The raw adverse control is under `installer-evidence/ps51-first-call-observation-fixture/foreign-create-parent-control/` in the original TAR. Its child PID is `5208`, nonce is `a9763c36e20d4332acdffe689c9b69b3`, and phase-stream SHA256 is `b353feeab4511a4799a3af49e490425a3e768bbe66593f1b07b9a1609789eef5`. The complete native receipt `ps51-first-call-observation.json` has SHA256 `ae7bd1bca733532f6b00af95915bd8fc1281b4678d7e6268279108d747a02cfb`.

The matched healthy control uses the same terminal pathname with the foreign-create grant removed, a separate fresh child and nonce, and succeeds in actual initialization and cleanup. It also records 32 compiler events before the old parent guard. This proves the observer discriminates the parent policy without making useful initialization impossible. The corresponding PS7 controls have zero observed pre-admission events in the monitored TEMP subtree; that is not a whole-process absence-of-effects claim.

**Required disposition:** a bounded native bootstrap must establish trustworthy ancestry and private compiler-output custody before compiler effects, with fresh-process native adverse and useful controls. The original first-call RED and probe must remain intact. A later bootstrap implementation needs its own actual boundary observation because legitimate private bootstrap effects may precede the old StageNative guard. This is an Important source/contract defect; the evidence does not establish an exploit or administrator/same-user isolation.

### Important — R15-NATIVE-05: PS7 mutation qualification stops at its prerequisite

PowerShell 7's unchanged-source baseline passes only 3 of 13 controls. Ten fail, principally with `CreatePrivateFile` exceptions. The driver exits 1, records `complete: false` and `FAIL_OR_ACQUISITION_GAP`, and creates or executes **no mutants**. Its stopping behavior is honest; none of the nine mechanisms receives mutation credit.

The current generic catch does not preserve the failing requested pathname, native Win32 error number, or immediate parent facts. Long nested paths are a hypothesis, not an established cause: PS5.1 succeeds with at least one longer observed download path. The independent review therefore declines to classify this failure as production versus fixture. A test-only delegate should capture path/length, exception chain/NativeErrorCode/HResult and parent native identity/ACL, then rethrow unchanged. Production changes require that causal evidence.

The separate native PS7 transaction28, custody8 and full-file normal consumers remain valid within their scope; they do not replace the failed prerequisite or unexecuted mutation mechanisms.

### Minor — R15-RECEIPT-01: non-ASCII path transport is not faithful

Both mutation baseline receipts record the fixture suffix as `-Øµ`, while the original TAR contains the same exact fixture GUID followed by `-ص`. The test constructs the suffix explicitly using `[char]0x0635`. `invoke_pwsh` captures `text=True` without a declared output-encoding contract and then serializes that decoded string; original pre-decoding stdout bytes are not retained.

The original filesystem bytes and the uniquely matching GUID/source-defined suffix allow bounded archival attribution, which the detailed review records explicitly. The records are not silently normalized. This is an acquisition limitation, not evidence that the installer changed the path. Preserve the old receipts and require a strict child/parent UTF8 contract, raw stdout/stderr preservation and a Unicode transport control for the next native increment.

## Corrections independently supported by this run

| Boundary | Actual native evidence | Scope |
|---|---|---|
| Directory lease — previous R15-NATIVE-01 | Both PS5.1 and PS7 refuse a live-root rename with Win32 sharing violation 32. Disposing only the root lease permits the same-root rename, preserving native identity, ACL and proof bytes, followed by restore/re-lease. | Exact `9e8fd3` access-bit correction; inspect-only handle behavior is unchanged. |
| Normal entry fixture — previous R15-NATIVE-02 | Four actual `-NoProfile -File` positive/NoOpen entries pass with valid PID/nonce, all interception phases, protected owned ancestor fixtures, unchanged external ancestor ACLs, equal browser snapshots and real retained configured preset/XPI/unpacked bytes. | Four normal rows only. Existing preview evidence remains separately source-scoped. Production ACL admission was not weakened. |
| PS5.1 transaction mutation mechanisms | All nine independently reconstructed mutants parse, fail the intended actual target and retain a useful healthy companion. The malformed-preset mutant records a real bad clipboard handoff; the global-rewrite companion records a real useful copy. | Actual native host, no POSIX adapter. PS7 earns no corresponding credit from this run. |
| Failure-stage controls | PS5.1 reaches actual File.Move collision after a complete retained copy; original TAR preserves the new full partial, collision sentinel, old archive/manifest/Unicode payload. Mid-extraction fails after the first member; late-member preflight records no member writers and leaves an empty output root. Both failed callers take truthful fallback without clipboard handoff. | Exact derived native fixture bytes and archived effects; PS7 prerequisite remains open. |
| Native Linux private export — previous R15-NATIVE-03 | Previously received native2 UID0 producer/UID1001 reader transfer preserves all ten original entries and separate embedded/copied manifest hashes. | Bounded prior independent review remains linked; no duplicate execution. |

Both native Windows hosts also pass components18, guards10, discovery78, transactions28 and custody8. Discovery mutations preserve the PS5.1 root-array-only survivor as uncredited; it is not converted to a pass. All source/test hashes are checked against the immutable candidate.

## No-installer timing observations

These four children per host are diagnostic acquisitions, with `installerExecuted: false` and `installerQualified: false`. The values below are parent-observed readiness times. Raw phase PID/nonce/counter streams and completed-cold-before-warm order are bound in the JSON. They establish measurements, not the cause of the delay.

| Host | Variant / iteration | Readiness seconds |
|---|---|---|
| ps51 | native-only-cold | 25.378 |
| ps51 | native-only-warm | 19.427 |
| ps51 | private-wildcard-cmdlets-cold | 19.382 |
| ps51 | private-wildcard-cmdlets-warm | 19.511 |
| ps7 | native-only-cold | 0.461 |
| ps7 | native-only-warm | 0.401 |
| ps7 | private-wildcard-cmdlets-cold | 0.511 |
| ps7 | private-wildcard-cmdlets-warm | 0.427 |

PS5.1 warm children still take approximately 19.4–19.5 seconds. The native-only cold child takes 25.378 seconds. No claim is made that warming eliminates the delay. Underlying timing diagnosis belongs to the separate host-bootstrap work.

## Complete denominator and remaining gates

The detailed JSON retains all **51 rows: 17 original, 9 residual, 18 November execution-scope and 7 terminal gates**. Current native evidence updates the existing obligations; it does not replace the original Bash, ownership, retention, public-delivery or campaign requirements with a Windows-only slice.

The unresolved engineering work is the compiler-custody correction with actual cold native validation, the PS7 mutation prerequisite cause and affected discriminating controls, and byte-faithful receipt transport. Revised source must be independently rebound and qualified at the actual changed boundaries, including useful normal callers and failure cleanup. The unchanged Bash/native lifetime and distinct-UID evidence remains scoped and retained.

Final source-linked README/manual-lifetime wording, public rendered/source/copy-command readback, final manifest and rollback/currentness remain necessary. Campaign predecessor/order conditions, exact entitled-owner approval, authorized merge, final public delivery, truthful full certificate and deliberate lifecycle closure remain root/owner gates. This review does not grant them.

## Evidence and limits

`native-run2-windows-review.json` contains 634 independently evaluated checks, exact source/instrument and top-receipt hashes, both lease pairs, four full-file observations, nine native PS5.1 mutation pairs, raw failure-stage checks, four first-call observations, eight timing rows, findings and every contract row. Its SHA256 is recorded above. `verify-native-run2-windows.py` is the attributed read-only verifier.

Prior original-contract/native reviews remain in this directory, including `publication-native-export-review-65410ae.json` for immutable publication and POSIX private-export closure. The old failed native attempts and first-call RED remain preserved; none is relabeled.

This review declines to determine the unrecorded PS7 native error cause, universal absence of process effects outside the watched TEMP subtree, exploitability, browser installation/reboot durability, or formal approval/lifecycle status. No source, shared tests, worktree/index/branch, remote or governor was mutated. Only the authorized original archive receiving and attributed reports/verifier were written.
