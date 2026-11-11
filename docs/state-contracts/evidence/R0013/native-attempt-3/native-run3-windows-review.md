# Independent R0013 native run 3 — Windows receipt and claim-scope review

Reviewer: `/root/r0013_review`. Ordinary attributed engineering review; no lifecycle or merge authority.

**Disposition:** Native Windows remains **FAIL**. Actual PS5.1 and PS7 component/discovery evidence and PS7 full-file entry are received at the reviewed bytes. The PS5.1 full-file acquisition gate remains open. No new installer source defect was established by this receipt review.

## Exact receipt binding

- Workflow run: `42978215112`.
- Commit: `6aefcd06673fc5d6dc76a33530d47320320b0d4f`.
- Tree: `f112393d4d4713a95828c3af9e7b8e6b614f4bc4`.
- PowerShell SHA256: `a67ac0c6190b3027a4ca31a1703df76b66558582e29b583bd15afe3da17bb7a4`.
- Windows ZIP SHA256: `b9de23c66e08ca57cd4f755a8cfde18903f327c0ff628cbcaa9f9e60fba68915`.
- Windows tar SHA256: `d231b88be886812a37ea3e278cdf85a871104d1b917a0cc794c2374a6d4cb0be`.

I compared the received zip/tar digests, verified the tar inside the zip, rebound every acquired source/instrument hash to the immutable Git blobs, and read every top-level receipt from the original tar as a regular member. I did not extract the archive or execute installer/native-host tests. The reviewed product remains ASCII and unchanged.

The native receipt identifies Windows Server 2022, Windows PowerShell `5.1.20348.5773` and supported PowerShell `7.6.6`. Their component receipts independently identify those versions and the exact source hash.

## Received native results

| Evidence | PS5.1 | PS7.6.6 |
|---|---:|---:|
| Components, exact-file parser and selectors | 18/18 | 18/18 |
| Guards and sentinel preservation | 10/10 | 10/10 |
| Actual discovery functions and callers | 71/71 | 71/71 |
| Detected discovery mutants | 10 | 11 |
| Exact-source healthy mutation prerequisite | Pass | Pass |
| Executed mutant retained without pass credit | 1 | 0 |
| Full `-File` entry | First case bootstrap blocked; remaining cases not run | 12/12 |

Both native component suites retain exact-file ParseFile and explicit-UTF8 parser controls with zero parser errors, ASCII source, selector ordering/suitability/rejection and actual caller/fallback controls. Native component evidence cannot replace the full-file entry gate.

## Important — R13-WIN-02 remains open

The first PS5.1 `github` DryRun call times out at 25 seconds. Its preserved fixture contains empty `stdout.txt` and `stderr.txt`, identical subject-before and subject-after snapshots, no recorded effects, no first wrapper phase file and no readiness marker. The driver reports `BOOTSTRAP_BLOCKED`, exits that host loop, preserves the complete fixture and continues the independent PS7 host. The overall Windows result stays FAIL.

The timeout-preservation repair is therefore demonstrated on the actual adverse native event. The blockage's cause is still undetermined. Absence of the first recorded phase does not prove that its statement was never attempted, identify a source defect, or identify the particular autoload/startup mechanism. There is no qualified PS5.1 complete-file result and no credit for the eleven cases that were never reached.

The next evidence needs to diagnose acquisition on the actual native host, establish all exported interception functions and the per-process nonce before qualifying the exact-file entry, then execute the required cases. Increasing the timeout alone would not establish causality or qualification.

## Host-specific mutation credit is preserved accurately

I recovered every intended one-site mutation from the immutable test driver's literal AST and compared all 22 native mutant files to that exact transformation, accounting only for Windows line endings. Their raw file hashes and receipt source hashes agree. Every original named assertion is still executed, and all healthy controls remain present and passing.

On PS5.1, the raw capability probe preserves the singleton JSON array as `System.Object[]`. Removing only the raw root guard is therefore protected by the separate production type check. Its actual mutant has exit 0, no failed cases and `detected:false`; it remains an executed non-discriminating applicability item and receives no mutation PASS. PS7 unwraps that same input to a scalar object, so the identical mutation is detected by the three original shape/caller assertions.

The actual PS5.1 downstream parser independently rejects the trailing commas and trailing comment used by the fixtures. Those original end-to-end assertions remain executed and passing when the strict guard is bypassed. The bypass still fails the single-quote, bare-key and duplicate-key mixed-caller assertions. Trailing-separator state mutations are detected on both hosts by direct calls to the actual production `Test-StrictJson`, with a passing valid-input control. PS7 also fails the end-to-end comma assertions. Protected results are recorded separately, not relabeled as killed mutations.

## PS7 complete-file entry scope

The actual `-NoProfile -File` commands address the complete immutable installer source. Eleven successful body-entry cases have raw positive numeric PID plus unique nonce markers, matching all five startup phases through `all-spies-exported`. The twelfth case is deliberate invalid parameter rejection before interception, with exit 1, no effects and unchanged subject state.

All preview and no-eligible cases preserve the subject snapshot and record zero installer effects. The separate host-home startup cache is retained as host startup state rather than silently treated as a product write. Normal and NoOpen cases retain the Chromium and Firefox assets and the selected-hash preset. Raw before/after snapshots confirm every preexisting fixture/profile entry is unchanged; all additions are under the fixture's temporary installer directory. Normal mode records 21 intercepted effects including four open calls. NoOpen records 17 effects with the same useful work and no open calls.

These are qualified fixture observations of the actual complete file, with external effects intercepted. They are not evidence that the browser extension installed automatically or that the user completed manual browser steps.

## Whole-contract disposition

The companion Apple/Linux report retains all 12 original parent rows, 7 residual children and 14 amendment rows. This addendum supplies actual Windows component/discovery and supported PS7 full-file evidence for the relevant ES13/R14 preservation claims. It does not discharge PS5.1 full-file entry, final delivery or campaign authority gates.

Remaining gates:

- Resolve PS5.1 full-file acquisition and receive all required exact-source native cases, retaining this failed run and the previous native attempts.
- Publish and review the final Bash and Windows README pins; bind public raw bytes, rendered documentation and copied/generated command paths to the qualified source.
- Preserve the separate R15 UID/interface proof boundary; the earlier invalid local `/tmp` foreign-owner premise receives no retrospective credit.
- Parent must establish campaign predecessors, currentness, exact owner approval, final integration and any merge/closure authority.

No Critical or Minor defect was established in this bounded review. The existing Important PS5.1 acquisition/qualification blocker remains open. The JSON report records all receipt hashes, per-mutant evidence, per-entry facts and 410 consistency checks. Those checks are artifact review, not additional native executions.
