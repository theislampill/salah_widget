# Original native Ubuntu22 acquisition — bounded receipt FINAL

## Disposition

**PASS for the bounded original-artifact receipt; GAP for R0016 preview qualification.** The original run is a terminal failure. Namespace/kernel controls succeed, then a later source-free readiness negative is blocked by two unattributed socket denials. The preview result contains **0 PASS, 0 product assertion failures, 1 BOOTSTRAP_BLOCKED**, and **0 preview product rows**. No event is removed or relabeled. The nine preceding suite reports retain their own successful results; this minimal receipt does not requalify every assertion in those suites.

## Original bytes and provenance

- Run **43127099817**, artifact **13903686554**, commit **a80558ae97ac2697ec6727356928dd7a394eee60**, tree **4a22496acdc19ff920fe64d508acea691fab6f79**. Original run/artifact APIs agree on the identity and failed conclusion.
- Original ZIP **765,582 bytes**, SHA256 `0cf87c269c6f7743596e96ce4f40be690af1db44ae19bb56e1639891be0631f4`, matching GitHub's original artifact digest. ZIP CRC passed.
- Inner TAR **810,687 bytes**, SHA256 `ffff6e37519aa6d6c61cf1ae4b7a082d72d14517315ca1bbe6d1f1654d76aca4`.
- **1,374** TAR members: **676** regular files, **691** directories, **7** symbolic links retained as metadata only. **3,336,433** regular bytes. All regular member hashes were independently verified. No links or archive code were executed. Fixture names containing a literal backslash were treated as POSIX filename components, not as path separators.
- All **34** recorded source hashes match published Git blobs at the exact commit. Retained actual `source.sh` matches installer SHA256 `d19ed5d90e1faf0d9ac66415814a3a68e28c6ae61730acd4eaef1b9588830cc5`; fixture SHA256 is `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00`. The source is unchanged. The top preview JSON, its raw stdout JSON, and the fixture's original results JSON agree exactly.

## Actual native host and outer suite results

The artifact reports Ubuntu **22.04.5 Jammy**, Linux **6.8.0-1070-azure**, x86_64, glibc **2.35**, Python **3.10.12**, Bash **5.1.16(1)-release**, UID/GID **1001**, runner image **20261101.347.1**. The prerequisite receipt is complete and all seven retained acquisition commands exit zero without timeout.

The original `install-bash`, entry, discovery, detector, discovery-mutation, original-mutation, builder, staging, and Linux-owner groups all exit zero, preserve their passing JSON reports, and have empty outer stderr. Each finishes within its 240-second bound. The final preview group runs from **00:25:38.054884Z** to **00:25:38.574517Z**, approximately **0.519633 s**, exits **2**, and has empty outer stderr. Its failure is retained in stdout JSON as `BOOTSTRAP: readiness discriminator had unrelated failure`.

## Kernel and command controls really succeeded

The original kernel-control stdout records PID **19383**, an allowed owned write, two denied outside writes (`new-file` and `sentinel`, both **errno 30 / EROFS**), and denied TCP/UDP creation (both **errno 1 / EPERM**). Its stderr is empty and the actual allowed-write file is retained. The 286-byte stdout has SHA256 `1948b02a668fd5e98e43e27a704aeca2d2c85606ef04f59d803702b2636b3c76`. Its raw network log contains **four** socket-denial records for PID 19383; the original three-field rows do not identify which two are the explicitly controlled TCP/UDP calls.

The subsequent command-denial control records PID **19388** and the exact nonce-bearing ready marker. It retains the `mkdir` event, expected denying stderr, and equal complete recorded subject snapshots. Its raw network log also retains **two** socket-denial records. Those extra events are not dropped merely because the command control's own stated assertion passes.

This outcome is materially different from the earlier Ubuntu24 namespace acquisition failures: actual native kernel containment controls reached and passed on this host. It does not justify changing or relaxing host policy.

## Later missing-readiness failure

The retained `readiness-missing` case has empty stdout and stderr, no ready marker, no command-event file, and byte-identical recorded before/after subject snapshots. Each snapshot is **1,964 bytes**, SHA256 `d46019e42d705b895e12872a279c0cb952457517c9dfbf2957983b30dec0f322`.

Its original raw network log is **128 bytes**, SHA256 `5f052635dd5647777ec00bd29733dc7acec7bd908fd5bdd29c4d7297aae2b421`, and contains exactly:

```json
{"pid": 19392, "syscall": "socket", "decision": "DENIED_EPERM"}
{"pid": 19392, "syscall": "socket", "decision": "DENIED_EPERM"}
```

The verified fixture source calls Bash `--noprofile --norc -c :` for this negative, with the readiness line removed from the bootstrap. Its composite assertion requires zero exit, equal snapshots, no command events, and no transport events before testing missing readiness. The two raw transport records explain a sufficient failing condition. **The original archive does not separately retain this child's return code or monotonic terminal/cleanup record**, so a per-child exit-zero or full lifecycle claim cannot be independently confirmed from these bytes. The directly retained outer harness terminal is 2.

No wrong-readiness case or product case follows. The actual fixture directory contains only the source, aggregate results, containment control, and the missing-readiness control.

## Required uncertainty and next bounded evidence

The original observer records no syscall arguments, address family, executable, command line, or readiness phase. These records cannot distinguish AF_UNIX from AF_INET, or Bash startup/NSS from later process activity. NSS/startup and unset USER/LOGNAME/SHELL are hypotheses, not findings. No host event is exempted and no absent global telemetry is treated as zero.

A separate source-free diagnostic that preserves all six denials and records raw six-argument, PID/executable, command-line, and readiness facts is a proportionate next observation. It must first demonstrate that its controlled post-readiness denied sockets are actually joined to those new records; C1's missing validation is documented in sibling `linux-startup-review/REPORT.C1.FINAL.md`. No original product fixture or host policy change is authorized by this receipt.

Evidence is retained in `archive-receipt.json`, original API response copies, `original-inner.tar.gz`, safely extracted regular members, `verification.json`, and `verify_received.py`. The data-only verifier completed **749** receipt consistency checks. No shared source, native workflow, run state, or host policy was changed by this lane; no overall acceptance, release, or closure is claimed.
