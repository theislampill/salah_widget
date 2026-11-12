# Linux owned-scaffold diagnostic C2 — focused independent rereview

## Bounded disposition

**PASS for the exact C2 source/receiver correction within this review's scope.** The original C1 permitted-capability adverse is preserved unchanged: C1 admits it, while C2 rejects it. All 20 independent focused replays meet their expected dispositions and preserve the complete input records. No remaining concrete blocker was found in the targeted correction.

This is a source/evidence-admission finding for root's next decision. No native Linux control, installer, namespace, network or browser execution occurred in this review. Actual root ownership, read-only mount behavior, capability state, six syscall denials, process cleanup and the two original normal results remain unacquired. No whole R0016 acceptance, publication or closure authority is exercised here.

## Exact current packet

| Item | Bytes | SHA-256 |
| --- | ---: | --- |
| Root C2 manifest | — | `4ebb7108200568860a8152fc8a30e18f1b3e59ae1bb775802f1e12e21b53134d` |
| C2 launcher | 34,941 | `ceefea319cfe596d4042de9af3411dd5f13daf53bb85c7b2e6276909c026933f` |
| Unchanged workflow | 3,981 | `93708abaeeb387d9a5347403ab47c03a39fb1230c823db968f36286bea627d84` |

All sixteen declared payloads match the frozen manifest. The workflow and five supporting source files are byte-identical to the independently reviewed C1 packet: product `d19ed5…`, preview fixture `6be6f8…`, original entry harness `d46dfc…`, lifecycle support `8051d5…`, and signed jammy preparation `adb7c4…`. Full identities remain in the manifests. The sole launcher delta is the enforcement-status parsing/admission block within `assess_control()`. Every other top-level AST node is unchanged; the complete textual diff was also inspected.

The original C1 report and its GAP are not overwritten. Its manifest remains `c7837497261ac6bfa66d543dfdee754d7a91d53386dc8a4699a72f0bdadfbb6c`; its exact permitted-set adverse remains SHA-256 `7355b1d55d4991baa154903fb9f1ac781b6ce362bb780091f0042d2ef6d55e13`.

## What changed and why it closes the finding

For both held-readiness and final child status, C2 now preserves the full raw text while requiring exactly one occurrence of each enforcement field: `NoNewPrivs`, `Seccomp`, `CapInh`, `CapPrm`, `CapEff`, `CapBnd` and `CapAmb`. Missing or duplicate fields fail before dictionary lookup can hide a contradiction. No-new-privileges must be 1 and seccomp mode must be 2.

All five capability fields must contain exactly sixteen hexadecimal digits after surrounding whitespace is stripped, and their numerical value must be zero. Empty, signed, short or nonhex masks fail. This directly rejects the retained adverse, which supplied zero effective capabilities but a nonzero permitted CAP_SYS_ADMIN bit. It also rejects nonzero inherited, bounding and ambient sets rather than inferring them from the effective set.

The operation does not rewrite, filter or normalize the retained input record. The focused replays compare the complete input structure before and after every predicate call and confirm it is unchanged. The correction adds observation requirements; it does not alter a namespace, mount, seccomp rule, host policy, product guard or source-free control operation.

## Independent and retained controls

The independent 20-case rereview executes only reviewed pure receiver functions under forbidden subprocess entry points. It covers:

- The exact retained C1 adverse, admitted by C1 and rejected by C2.
- Complete healthy observations, admitted before and after the adverses.
- Each of the five nonzero capability sets at each of the two phases, all rejected.
- A missing permitted field at either phase, both rejected.
- Contradictory duplicate no-new-privileges, seccomp and permitted-capability fields, all rejected.
- A malformed permitted-capability mask, rejected.

The author's original 52 predicate cases and 23 static checks also pass when replayed in an owned copy. The only healthy-fixture change supplies all five complete zero capability fields. The separate 31 author capability controls pass, including the preserved C1 false accepts, C2 rejection at both phases, all five nonzero masks, missing/malformed fields, contradictory duplicates and restored healthy input. The copied author test's C1 read path was redirected to the reviewer's identical frozen C1 module; this sole scaffolding adjustment is documented in `author-replay-adaptation.json`. No assertion was changed.

These results demonstrate the bounded correction and preserve the earlier useful controls. They do not convert synthetic evidence into native containment credit.

## Unchanged scope and limits

The scaffold remains a newly owned sibling outside the only writable ordinary fixture bind, mounted read-only at guest `/`. System directories and inputs remain read-only, private PID/network/user/mount boundaries and the six original seccomp denials remain unchanged, and the host-proc alias/write controls are unchanged. The C1 review's owned-filesystem control already established that the allegedly absent sentinel leaf does not falsely satisfy the write-denial probe: the exact `O_CREAT` operation attempts creation and the receiver rejects a writable exposed root.

Both source-free controls still run before any product case. They retain exact readiness/PID/namespace/argv association, raw syscall records, complete status and mount facts, allowed/denied write controls, bounded terminal/capture/cleanup records and full inventories. Only then may the unchanged original normal and NoOpen interfaces execute. Source binding, the original installer guard, normal harness assertions and the fixed two-case denominator are unchanged. The original eight failed Linux normal/companion observations remain failed historical evidence.

Native acquisition may still reveal that the proposed command or host does not provide the required all-zero capability sets or another required observation. Such an actual result must stop the normal pair and remain a failed/incomplete discriminator; this source finding does not predict the result. A future two-case success would still not qualify the full 45-case matrix, its six mutant companions, earlier failed rows or overall R0016 acceptance.

## Review evidence

`independent-results.json` records the twenty exact dispositions, unchanged-input checks and source identities. `verification.json` records packet/source/control bindings. `REVIEW-MANIFEST.json` binds this report, the preserved original adverse and the replay outputs. All review writes remain under the assigned owned scratch directory.
