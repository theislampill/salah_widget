# Linux owned-scaffold diagnostic C1 — independent source/receiver review

## Bounded disposition

**GAP: one evidence-admission correction is required before this packet is treated as a completed containment discriminator.** The exact C1 receiver admits a status record with a nonzero permitted capability set while the effective set is zero. The full intended `--cap-drop ALL` state is therefore not checked before `OBSERVED` is returned and the caller proceeds toward the original normal pair.

This is a source/receiver finding. No actual retained capability, namespace escape, native ownership result, or successful normal product case was observed or inferred. The reviewer did not author this proposal and made no repair to proposed or shared source. Root retains exclusive shared-source, publication and native-dispatch authority.

## Frozen packet and provenance

| Item | Bytes | SHA-256 |
| --- | ---: | --- |
| Proposal manifest | 5,992 | `ea4f4e065314a5ad36335a2b6d059f9ebd62c357e4ebbfe27554f48b9eab9de3` |
| Author report | 13,906 | `55741310c7cdb167567e832a52fb3cbc5fb385962531bbd0eb713dcac9628733` |
| Proposed launcher | 34,529 | `5b877b2d2b42ea4232ffa0d464cfad8f37c14a4fccd1269f11c38c86acfcf8a1` |
| Proposed workflow | 3,981 | `93708abaeeb387d9a5347403ab47c03a39fb1230c823db968f36286bea627d84` |

All 33 manifest payloads, totaling 2,245,690 bytes, were copied into the reviewer's owned scratch with exact size/hash checks. The frozen copy remains separate from write-required inert test copies. The five unchanged dependency files match immutable Git objects at the stated context commit `f25ea95d68d9257d1177d4d87f99d045df88b89a`.

The product remains `d19ed5d90e1faf0d9ac66415814a3a68e28c6ae61730acd4eaef1b9588830cc5`; preview fixture remains `6be6f8109ce0e219b1bbc124aecde8c59190fffbb5c9e490d8beffa1ecce415e`; original normal harness remains `d46dfc53b61406d18883a08cd77a0788ed2b46131904329c7dded865e214b093`. The namespace lifecycle support is the exact reviewed `8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328`, and jammy preparation is `adb7c47a6416b51bf96b6647e500bfba4e2d206a50a408a0e331f16d61ea9161`. The support module's old launcher and old harness pin are not used by the new controller; only its lifecycle, identity, binding and inventory helpers are called.

The original failed Linux ZIP was independently rejoined to the retained inner TAR: ZIP 1,094,503 bytes, SHA-256 `14ebef80c36947ee1ed7339a1760ea41217871fdde86bf0bc375be9578b28e0f`; inner TAR 1,184,038 bytes, SHA-256 `ee1e9d4d9a3c793d7ebffd0b4156bbcba30ec1c8617ebaa8a220b4b6b01ea4c8`. The archive iteration confirms 2,973 members and 1,363 regular files; all ten selected original records in the packet match the original TAR streams. The original 37 PASS / 8 PRODUCT_ASSERTION_FAILED / 0 BOOTSTRAP_BLOCKED partition and all eight `Untrusted ancestor owner: /` errors remain intact. Child-visible root ownership was not measured by that original failure and remains a hypothesis to be tested.

## Concrete finding: permitted capability set is ignored

The exact `assess_control()` gate parses both held-readiness and final child `/proc/self/status` text, but its capability check only converts `CapEff` and requires zero. It does not require `CapPrm`, `CapInh`, `CapBnd` or `CapAmb` to be present or zero.

The independent adverse keeps the healthy source-free observation, exact namespace/UID maps, nonce, PID association fields, read-only write results, six errno-1 syscall results, six matching denied observer records and Bash result. Both status records retain `CapEff: 0000000000000000`, while they additionally report:

```text
CapInh: 0000000000000000
CapPrm: 0000000000200000
CapBnd: 0000000000000000
CapAmb: 0000000000000000
```

The nonzero bit is the permitted CAP_SYS_ADMIN bit. The exact C1 `assess_control()` nevertheless returns `status=OBSERVED` and accepted home/temp guard interpretations. This demonstrates a receiver accepting evidence inconsistent with its declared dropped-capability boundary. It does not demonstrate that the actual proposed command would retain that capability. The controller invokes this same predicate before appending a successful source-free control and before entering the optional normal pair; the finding concerns a real admission gate, not an unused helper.

The minimal recommended revision is an explicit, present, well-formed zero check for all five declared capability sets (`CapInh`, `CapPrm`, `CapEff`, `CapBnd`, `CapAmb`) in both retained status records, preserving the full original status text and existing no-new-privileges/seccomp checks. Healthy inert fixtures must supply those fields, and the retained nonzero-permitted adverse must reject. Root has accepted this bounded correction direction. No fixture, policy, mount or installer assertion needs relaxation.

Exact adverse data is retained in `permitted-capability-adverse.json`; the operation and its actual false acceptance are in `independent_inert.py` and `independent-inert-results.json`.

## Source and containment review otherwise established

The constructor keeps unprivileged user and network namespaces, read-only host-root or read-only owned-scaffold selection, a private PID namespace, and explicit capability dropping. The scaffold is a fresh owned sibling outside writable fixture ROOT. Its newly created directories are made private; existing host ancestors are not chowned or chmodded. System directories, copied inputs and the owned outside sentinel are read-only binds. There is exactly one ordinary writable bind, the original absolute fixture ROOT; private `/proc` and `/dev` remain separately declared runtime filesystems. No host sysctl, AppArmor, ACL or product trust guard is changed by the new route.

The source-free control contains no installer execution. Its trusted-parent interpretation corresponds to the source-pinned owner, mode, directory and physical-path decisions for the generated canonical ancestor chains; the report labels it as interpretation. Actual product-guard behavior comes only from the later original normal cases.

The six original seccomp-denied syscall names remain exact and unchanged: socket, socketpair, connect, sendto, sendmsg and sendmmsg. The control invokes each explicitly, requires integer -1/EPERM results, and requires exactly six ordered matching observer records for the held child PID. Extra, missing, wrong-PID or allowed records fail. Readiness requires the nonce and one exact parent-observed namespace/NSpid/argv association in the launched ancestry. The source retains complete parent-read identities and child status text.

Only after both source-free controls are admitted does the controller select the five exact existing fixture function definitions needed for `normal()`. It then calls only normal and NoOpen through the unchanged `--positive-child` interface and unchanged original PTY harness. Product, fixture and harness pins are copied and checked; original/copy bindings are checked again at the end. The complete 45-case preview matrix and its six normal companions are not run or qualified by this route.

Each source-free phase is capped at 30 seconds and each original normal phase at 60 seconds, with bounded owned cleanup through the pinned support helper. The terminal gate checks exact command, integer exit, monotonic launch/deadline/terminal relations, natural cleanup, no forced signals/errors, direct-exit agreement and no remaining direct descendants. Captures go directly to files and are bounded at 4 MiB each. Complete two-pass fixture inventories, scaffold/outside comparisons and final input/executable checks remain required. Archive creation preserves regular files, directories and link metadata without following symlinks.

The workflow uses a distinct noncancelling concurrency identity, Ubuntu 22.04, a 12-minute job cap, read-only contents permission, exact commit checkout, and pinned checkout/upload actions. The existing signed jammy preparation is separate from the new route. Its declared APT cache/index retention policy does not exclude any diagnostic fixture, capture or event. Always-attempted archive/upload preserves partial results; external runner cancellation can still prevent a complete artifact.

## Meaningful inert checks and a corrected initial suspicion

The author's exact inert suite was replayed in a separate owned copy: **52/52 predicate cases and 23/23 static checks passed**. Its write-required synthetic records did not overwrite the frozen packet.

Eight additional independent checks were run against the exact proposed module, with subprocess entry points forbidden. Seven met their expected disposition; the eighth is the capability false acceptance above. The passing checks include the healthy scaffold, missing sixth transport denial, wrong child PID, merely absent direct read-only path, unexpected writable alias mount, missing allowed-write proof, and an exposed root with a previously absent sentinel leaf.

An initial review suspicion concerned the host-PID probe's guest-only sentinel leaf. It was disproved after inspecting and exercising the exact `write_probe()` function: `os.open` includes `O_CREAT`. A missing leaf under an exposed writable root therefore causes a write attempt rather than an ENOENT result. An owned scratch filesystem model, with a synthetic proc-root symlink pointing only within reviewer scratch, created that previously absent leaf; the exact receiver rejected the returned successful-write observation. The model never used actual host `/proc` paths or namespaces. `absent-leaf-probe.json` preserves this correction. Direct read-only sentinels require EROFS, so a merely absent direct target is independently rejected.

No installer, Bash, network or namespace process was executed in this review. No native capability escape was attempted. The only executed proposal portions were reviewed pure receiver/constructor logic and the small file-I/O probe restricted to newly owned scratch paths. No other concrete source blocker was found within this bounded review.

## Next evidence boundary

This C1 packet remains **GAP**, pending the minimal capability-receiver correction and focused independent rereview. After an accepted source revision, actual native ownership maps, mount semantics, host-proc alias results, six actual denials, lifecycle records and the two original normal cases still require original-artifact receiving. Neither this review nor a future two-case success retroactively changes the original eight failed cases or supplies whole R0016 acceptance.
