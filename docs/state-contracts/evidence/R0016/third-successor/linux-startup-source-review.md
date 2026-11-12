# Linux startup diagnostic C2 — independent source review FINAL

## Bounded disposition: PASS

C2 resolves the specific C1 acquisition gap. The revised caller now requires the controlled native stdout to join the newly recorded syscall telemetry before it can set `semanticCaptureComplete=true` and `acquisitionComplete=true`. No further blocking issue was found within this two-file source-free diagnostic proposal. This is source qualification only: no native run, original product fixture change, host-policy change, product acceptance, or overall R0016 closure is established.

The prior C1 NEEDS_REVISION report and all its counterexamples remain frozen in `REPORT.C1.FINAL.md` and `c1-gap-reproduction.json`.

## Exact frozen inputs

| Item | SHA256 |
|---|---|
| C2 manifest | `4f9480ea3824dedd543f462265e9cffd1035742d68893f9887bb7df575dfecc6` |
| Proposed probe, 17,964 bytes | `b5b0e03df6293661ad7242e0ae1f00036d53dbe0daf8c2543461cafc9b59967c` |
| Proposed workflow, unchanged | `4e4d56dc8ba771b4a260a3bb58a4ff7d55b1398669ad292987ff8ffe1e2155e7` |
| Derived observer, unchanged | `f77670dc2aa5fa9b0aa9c00b59d88965007c55caaf3e28845f7ff16e8f886928` |
| Published fixture, unchanged | `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00` |
| Namespace/lifetime/inventory support, unchanged | `8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328` |
| Ubuntu22 prerequisite helper, unchanged | `adb7c47a6416b51bf96b6647e500bfba4e2d206a50a408a0e331f16d61ea9161` |

Every manifested file was verified and copied into the reviewer-owned `candidate-2/` snapshot. The workflow, four base inputs, and derived observer are byte-identical to C1. C1 already bound the base files to the published `a80558ae97ac2697ec6727356928dd7a394eee60` sources.

An independent AST comparison confirms that the only executable source additions beyond C1 are the `socket` import, the new pure `validate_controlled_transport` function, one prelaunch physical Python binding, one actual invocation of the new gate inside the semantic-acquisition try block, and one post-case binding equality check. Removing exactly those additions reproduces C1's AST. The four fixed cases, original capture/lifecycle handling, read-only host bind, owned writable fixture, all six syscall denials, EPERM response, raw logging, namespace construction, cleanup, and artifact retention remain unchanged.

## What C2 now requires

For the explicit transport control, the gate selects observations using both the control's reported PID and the independently recorded physical Python executable. This handles Bash exec without assuming that a PID always names the same executable. It requires exactly three selected records in the declared UNIX-stream, INET-stream, INET-datagram order. Every selected record must retain:

- `socket` and `DENIED_EPERM`, the exact controlled PID, and the independently captured initial Bash PID;
- six unsigned 64-bit integer arguments, correct address family and protocol, and either the plain expected socket type or that type with only the explicitly admitted CLOEXEC bit;
- a monotonic notification timestamp within the launch-to-first-terminal interval;
- exact readiness bytes containing the captured Bash PID and case nonce;
- the exact `/usr/bin/python3` plus control-file command line, with matching retained bytes and hash;
- retained process-stat bytes with a matching hash and PID, and a consistent process start tick across all three records.

The physical Python binding is taken before launch and rechecked after the case. A missing record, extra same-PID Python record, malformed metadata, incorrect tuple, wrong nonce, inconsistent process identity, out-of-interval notification, or changed interpreter binding prevents acquisition. Earlier Bash rows remain in the original list even if Bash and Python share a PID. No raw row is filtered out of the receipt or automatically attributed to NSS/startup.

## Independent caller verification

The independent check isolates the exact candidate's `digest`, new predicate, and `run_case` AST definitions and supplies inert reviewer-owned dependencies. No subprocess, namespace, shell, socket, installer, or archived code is executed. This verifies the actual caller's acceptance behavior, rather than checking the helper in isolation.

All **13** targeted cases produced the expected result:

| Inert case | Expected and actual acquisition |
|---|---|
| Valid CLOEXEC control | Accepted |
| Valid plain socket types | Accepted |
| Same-PID Bash-to-Python exec, two earlier Bash rows retained | Accepted; all five raw rows retained; Python indexes 2, 3, 4 |
| Missing log — original C1 counterexample | Rejected |
| Wrong controlled PID — original C1 counterexample | Rejected |
| Wrong socket family — original C1 counterexample | Rejected |
| Wrong readiness nonce — original C1 counterexample | Rejected |
| Extra same-process Python row | Rejected |
| Inconsistent process start tick | Rejected |
| Notification before launch | Rejected |
| Wrong command-line hash | Rejected |
| Boolean in an unused syscall argument slot | Rejected |
| Physical Python binding changed after launch | Rejected |

All supplied rows remain present in every case, including rejected cases. The C1 inert dependencies were transparently updated with a deterministic physical Python binding and valid synthetic command-line/stat byte/hash fields required by the repaired gate. A separate adversarial case deliberately changes the binding. These scaffolding changes are documented in `c2-inert-verification.json`; no candidate logic was replaced in the replay.

`c2-source-verification.json` retains **23** source/manifest consistency checks. `c2-inert-verification.json` and `check_c2_inert.py` retain the independent 3-healthy/10-adverse caller verification. The author's separate 21 checks were retained as packet data; this disposition does not depend on their reported outcome.

## Scope after review

The four-case diagnostic can acquire richer source-free evidence on the exact native Ubuntu22 host while leaving the original failed Linux22 run and all denials intact. Whether the default and explicit environments differ, and whether any extra socket record belongs to Bash or a particular library/startup operation, remains a question for the original future native captures. A source-free observation is not a product row. Missing global telemetry is not counted as zero.

The original Linux22 receipt remains independently bounded at sibling `linux22-native/REPORT.FINAL.md`: kernel controls succeeded, the later readiness negative was blocked, and no preview product row ran. This review grants no dispatch, publication, merge, release, readiness, or closure authority to this receiving lane. Root retains source custody and publication authority.
