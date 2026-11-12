# Linux fixture identity addition — independent source review FINAL

## Bounded disposition: PASS

The frozen proposal is exactly one Linux-only identity block in `fixture()`, immediately after construction of its explicit environment and immediately before return. It provides the tested native namespace identity before Bash launch. It does not change production source, transport policy, event admission, snapshots, readiness assertions, or any case selection. Actual qualification of the changed fixture remains pending native execution.

## Exact packet and change

- Manifest SHA256: `faa680b9d7213eec92efba84131b5076ca4f23b00d274a865487743093cb5276`.
- Original fixture, **59,830 bytes**: `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00`.
- Proposed fixture, **60,074 bytes**: `6be6f8109ce0e219b1bbc124aecde8c59190fffbb5c9e490d8beffa1ecce415e`.

The complete addition is **244 bytes**, including its two-line explanatory comment. Its executable content is:

```python
if HOST == "Linux":
    env.update(USER="root", LOGNAME="root", SHELL=ARGS.bash)
```

Removing exactly that block restores the original file byte-for-byte. Removing its one `if` node restores the entire original AST. The block follows the explicit environment dictionary and precedes the return, so it supplies these fields to subsequent fixture launches; it does not inherit ambient host identity. Darwin does not enter the new branch. A separately selected Linux Bash path supplies its own `SHELL` value rather than a substituted interpreter path.

The existing namespace maps the caller to UID 0 using `--map-root-user`. Native diagnostic run **43129938581** independently records the actual root account at UID 0 and tests the same root/root/Bash tuple with the selected `/bin/bash`. That diagnostic's post-readiness positive control still records all three denied UNIX/INET socket attempts. The original production installer remains SHA256 `d19ed5d90e1faf0d9ac66415814a3a68e28c6ae61730acd4eaef1b9588830cc5`; this proposal contains no production edit.

## Preservation checks

The complete early `--sandbox-child` prefix is byte-identical. All six syscall names and the original EPERM response remain unchanged. So do the read-only host bind, owned writable fixture, cleared environment, namespace flags, original `sandbox_run`, full snapshot and evidence functions, `no_effects`, both missing/wrong readiness negatives, bootstrap controls, actual preview entry and interrupted-entry checks, normal/NoOpen cases, and mutation machinery. There is no cache clearing, PATH masking, event filtering, new exception, or host-policy relaxation.

An independent static enumeration of the actual all-suite campaign confirms identical case names and categories before and after:

| Host | Bootstrap | Helper | Entry | Interface | Normal | Mutation | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Linux | 1 | 12 | 17 | 7 | 2 | 6 | **45** |
| Darwin | 1 | 12 | 18 | 7 | 2 | 6 | **46** |

Darwin's additional literal zero-target refusal is preserved. These are **static denominators conditional on successful bootstrap**, not newly executed PASS results. No candidate function or native product case was executed by this review.

## Evidence and limits

`verification.json` records **27** independent manifest, byte, AST, protected-function, native-identity association, and case-denominator checks. `verify_source.py` contains the data-only verifier and restricted AST campaign enumerator. The immutable reviewed packet is retained under `candidate-1/`.

The supporting source-free native result establishes the behavior of the identity tuple as a group. It does not isolate an individual variable or identify an NSS mechanism or socket address. No inference of that kind is needed to preserve the full native identity and retain every existing denial. The original Linux22 failure, C1 diagnostic rejection, C2 source review, and original C2 native receipt remain separately retained.

This is bounded source qualification only. The changed fixture requires fresh actual Linux and Darwin receipts, and no overall R0016 readiness, product acceptance, merge, release, or closure is asserted. Source custody and publication remain with root.
