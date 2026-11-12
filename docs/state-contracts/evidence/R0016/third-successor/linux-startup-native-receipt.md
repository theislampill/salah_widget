# Original Linux startup diagnostic — independent receipt FINAL

## Bounded disposition: PASS

The original four-case source-free diagnostic is received intact, and its actual raw captures satisfy the reviewed C2 acquisition conditions. All four cases terminate naturally within their budgets, preserve complete owned-child cleanup, retain every observed socket-denial row, and reconcile with their nonce-bound captures and full inventories. **Product rows executed: zero.** This receipt does not qualify a product fixture change or infer an NSS mechanism, socket address, or global absence of transport attempts.

## Original custody and source

- Run **43129938581**, artifact **13904986495**, commit **dab4b81b2eb926043e47c69a207601939b8128a1**. Independent read-only GitHub run and artifact GETs agree on exact identity, original digest, and terminal success.
- Original ZIP **43,024 bytes**, SHA256 `679a0859482a1893963edc0942627cf015167289386ee5adb2a492edad1b063b`; ZIP CRC passed.
- Inner TAR **43,228 bytes**, SHA256 `90d3939274fa7aed053a6a0124018951cd0fd183ac16abb261f3245589c0da9e`.
- **91** TAR members: **66** regular files, **25** directories, no links, **240,757** regular bytes. All received regular bytes match the original member inventory. Extraction was confined to reviewer scratch; no archived code was executed.
- All four source bindings match their exact published Git blobs. Probe `b5b0e03df6293661ad7242e0ae1f00036d53dbe0daf8c2543461cafc9b59967c`; original fixture `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00`; support `8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328`; Ubuntu22 prerequisite helper `adb7c47a6416b51bf96b6647e500bfba4e2d206a50a408a0e331f16d61ea9161`.
- Published workflow matches the reviewed `4e4d56dc8ba771b4a260a3bb58a4ff7d55b1398669ad292987ff8ffe1e2155e7`. Retained original harness, derived observer, and Python control exactly match the reviewed derivation and literal control source. Observer SHA256 `f77670dc2aa5fa9b0aa9c00b59d88965007c55caaf3e28845f7ff16e8f886928`.

## Actual host, commands, and process completion

The original host records Ubuntu **22.04.5 Jammy**, Linux **6.8.0-1070-azure**, x86_64/glibc **2.35**, UID/GID **1001**. Controller PID **2290** confirms its process-local child-subreaper state. All seven original prerequisite commands terminate zero without timeout.

Every actual launch exactly matches the reviewed `unshare --user --map-root-user --net` and bubblewrap command: read-only host root, one owned writable fixture, explicit `/proc` and `/dev`, cleared environment, fixed `/usr/bin:/bin` PATH, pinned observer, and source-free Bash/control argv. There is no installer argument. All four recorded Python bindings match the same physical `/usr/bin/python3.10`; Bash records physical `/usr/bin/bash`.

| Case | Launch PID | Bash PID | First terminal observed | Complete measured interval | Raw socket rows |
|---|---:|---:|---:|---:|---:|
| default-no-ready | 2293 | 2296 | 131.971085 ms | 0.132881171 s | 2 |
| default-ready | 2297 | 2300 | 102.172959 ms | 0.103020265 s | 2 |
| explicit-ready | 2301 | 2304 | 101.656143 ms | 0.102901229 s | 0 |
| explicit-transport | 2305 | 2308 | 132.330483 ms | 0.133261331 s | 3 |

Every terminal is integer **0**, first observed before the **30-second** monotonic deadline. Each case's unchanged cleanup protocol has a **five-second** budget and reports complete cleanup, direct exit zero, no signals, no errors, no adopted-child reaps, and no remaining direct owned children. This is an owned-descendant observation, not a global process inventory.

Raw stdout is **52, 52, 52, and 269 bytes** respectively, with all four stderr captures empty. Every capture size/hash matches its recorded binding and remains below the one-MiB limit. Each neutral line binds actual Bash PID to the unique case nonce. Every raw case result equals the corresponding top-level row, and each launch record reconciles with its final case record.

## Actual differences between the four cases

The default cases omit USER, LOGNAME, and SHELL. The explicit cases set **USER=root, LOGNAME=root, SHELL=/bin/bash**. The selected Bash path is `/bin/bash`, and the native account fact records the namespace's root account with UID 0. All other declared environment differences are the intended readiness/control paths and unique case-local values; the full exact environments are retained.

Both default cases record exactly two `socket` notifications from their actual `/usr/bin/bash` executable, with first three arguments **[1, 526337, 0]**, decision **DENIED_EPERM**, and a missing readiness file at notification. All six raw arguments, process-stat and command-line bytes/hashes, executable paths, initial child PIDs, and monotonic timestamps are retained and independently verified. Family **1 is AF_UNIX**. The default-ready case later writes the correct readiness token. The no-ready case intentionally never writes one.

The explicit-ready case retains **`transportAttempts=[]` and `transportLog=null`**, with no corresponding log file, a correct ready token, empty stderr, and unchanged full subject snapshots. This is the observed result of the retained six-syscall observer for this bounded source-free case. An absent log is not invented as a zero-byte hashed file, and this observation supplies no global network telemetry or product acceptance.

The explicit-transport case demonstrates the repaired C2 join on actual native bytes. Bash PID **2308** is reused by physical **`/usr/bin/python3.10`**, and all three retained rows identify that executable and exact control-file argv. Their ordered first three arguments are:

1. **[1, 524289, 0]** — UNIX stream with CLOEXEC.
2. **[2, 524289, 0]** — INET stream with CLOEXEC.
3. **[2, 524290, 0]** — INET datagram with CLOEXEC.

All three are denied with EPERM after the exact **2308 + case nonce** readiness token exists. Their stat records agree on start tick **3067**. The independently reconstructed proof exactly matches the recorded raw indexes **[0,1,2]**, three retained rows, physical Python path, command/readiness hashes, and normalized socket-tuple order. No earlier or extra event is discarded.

## Filesystem and positive-control observations

All **16** before/after inventory files are complete two-pass records with matching passes. They retain root and all entries, kind, ownership, mode, device/inode/link count, sizes, nanosecond mtime/ctime, and regular-file hashes. All four outside-control before/after inventories match exactly. The three neutral subject inventories also match exactly.

The controlled subject inventory is intentionally unequal: the only changes are the new `home/allowed-write` containing the exact nonce and its parent `home` metadata. This expected effect is preserved, not exempted from the snapshot. The original Python control reports the outside write denied and its owned write allowed. Its outside-denial Boolean is retained; that control does not separately serialize the specific outside-write errno.

## Interpretation limits

This source-free run establishes an observed difference between the default environment and the **three-variable identity tuple tested together**. It does not identify which individual variable is sufficient, a particular NSS/library call, a socket pathname or remote address, or the call stack that caused the default Bash attempts. A denied `socket` creation does not reveal a later connection target.

The native executable byte hashes are recorded metadata; executable binaries are not included in the archive. The review independently checks all retained bytes and bindings without claiming to rehash an unavailable native executable. Source-free success is not a product row, and workflow success alone supplies no product qualification. The original failed Linux22 preview artifact remains unchanged.

Evidence: `archive-receipt.json`, original run/artifact API bodies, `original-inner.tar.gz`, safely extracted original regular files, published source copies, `verification.json`, and `verify_received.py`. The independent data-only verifier completed **268** consistency checks. No shared source, workflow state, or host policy was modified by this lane.
