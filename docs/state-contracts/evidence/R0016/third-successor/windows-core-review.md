# Independent Windows receiver review — core2

Report state: FINAL. Disposition: **PASS for the bounded command/driver association repair**.

The exact new receiver closes findings WNR-01 and WNR-02 from core1. This report covers the repaired v2 qualification-instrument receipt predicates and their wiring to the existing actual, baseline, carrier, and guard paths. It is not native execution, installer product acceptance, or full-contract acceptance. This is a NEW repair of preserved core1; it is not a reproduction or recovery of the missing historical final core3 receiver. All earlier failures and provenance limitations remain historical evidence.

## Independent review context

Reviewer: `/root/independent_review`. Requested model: inherited parent model; no override requested. Actual model: host-declared GPT-6 Astra Pro; the host exposes no more specific provider deployment identifier. `authoring_context_reuse: no`.

I authored none of the reviewed receiver, producer, libraries, or standalone carrier. I read the actual patch, affected functions, call paths, and test code before the author's report. All replay writes are under `/tmp/r0016-third-20261111/work/independent_review`. The additional independent replay forbids subprocess entry points. No installer, PowerShell, Windows host, or GitHub workflow was executed. I made no shared-source or Git mutation and exercised no publication, dispatch, acceptance, or closure authority.

## Exact received packet

Frozen source: `/tmp/r0016-third-20261111/work/windows_recovery/core2/frozen-core-2`.

Manifest SHA256: `7631dbdaed3ad99d18d0535c454edc1c36f629177d99c1147298c07472af85ba`. I verified the full inventory and every payload length and digest: **21 payloads, 302,370 bytes**. Tests ran only after copying the verified packet to `/tmp/r0016-third-20261111/work/independent_review/windows-core-candidate2/packet`.

| Item | Bytes | SHA256 |
| --- | ---: | --- |
| New core2 receiver | 57,571 | `c0f1dccae4a0e7f73867a6aa8c8d2ef8a76cd59e27e4edfcb6f4499d317e7978` |
| Preserved core1 receiver | 55,032 | `851cf29917ed0ced30e7ebd1195f49de430b6f5bdf02d7fbc1643ce8af9889df` |
| Full receiver patch | 12,442 | `2410f00656cfa3a59a0c5e54bdf519bfd15268a47457fb319e3a5d512109c9ba` |
| Unchanged producer | 57,909 | `e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916` |
| Unchanged acquisition library | 22,009 | `b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1` |
| Unchanged window library | 13,117 | `05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83` |
| Unchanged standalone carrier | 13,102 | `733ff1ebc15b6e83e319313c33cbf67a888763a27388155d52ebe0e7c0497e04` |
| Preserved actual embedded driver | 14,582 | `d81ce7e94bb1545acff16c080e0c8fa136bef02dc857bfafe2b44fdeb5b9bc50` |
| Author report | 6,173 | `5d88c6994a20410b5395501e77927444f8dffe32efc9a9cd3ec5da60270406b8` |

My receipt is `/tmp/r0016-third-20261111/work/independent_review/windows-core-candidate2/receipt.json`, 3,787 bytes, SHA256 `278d16ce4150ca899566fc791332e2791b18e537c2979e8bd6fce2e5ebfed62c`.

The packet preserves the original independent adverse JSON exactly: SHA256 `c5390497ca6a03c782dcafab529c153b8db7ad703a4c2a278661d7ebe5bcea41`. The immutable core1 FINAL GAP-REVISE report remains `/tmp/r0016-third-20261111/work/independent_review/windows-core-review-candidate1.md`, SHA256 `518a00648bf358f65945e2706f126cb2f1f83c7c9dec6c953444dcbc7365f0cd`.

## Repair and source-to-driver join

V2 preflight first verifies the supplied producer's digest against the receipt's test identity. `verify_embedded_driver` then requires one maintained literal-driver span and the expected `preview-child.ps1` declaration, derives its exact UTF-8 bytes, and compares them to the owned retained `core_root/preview-child.ps1`. The resulting absolute path, byte length, and SHA256 fact is passed into subsequent launch checks and retained in both the returned plan and custody set. The actual derived bytes agree with the preserved 14,582-byte driver above.

`verify_driver_launch` validates that bound fact against the file, requires an explicit absolute process nativeFile equal to its path, requires the raw launch nativeFile to equal that path, and compares raw arguments against the exact maintained `-NoProfile -File` constructor. The constructor matches the unchanged PowerShell acquisition and held-window functions. Neither absent fields nor a matching alternate self-declared path can become the expected driver.

The actual and source-free baseline calls in `verify_case_files`, each of the six carrier calls in preflight, and all four guard calls receive this producer-derived fact. Actual/baseline held-window spec, source, subject, nonce, PID, label, host, and snapshot associations remain required. The driver itself joins the held proof paths and final custody verification. I inspected these actual call paths and the static checker independently confirms explicit expected-driver arguments at every relevant call site.

Historical v1 dispatch remains separate. The held-window driver requirement is enabled only for v2; the explicitly tested legacy full-lifecycle and omitted-drain compatibility behavior remains. No v1 case field can opt itself into the v2 held-window semantics.

## Findings resolved by actual replay

Core1 WNR-01 accepted wrong or missing actual/baseline/guard raw arguments. WNR-02 accepted absent nativeFile in both process and raw held launch claims. The frozen eight original defect probes were replayed against both exact generations: **core1 accepts every adverse, and core2 rejects every adverse**.

I also constructed a separate receiver replay using the actual `verify_case_files`, `verify_guard_launch`, and `verify_invocation_window` functions, with updated raw launch file facts. It contains three healthy cases—actual with baseline, guard, and carrier—and twelve adverse cases. Each of the four roles independently receives missing arguments, a substituted `-Command`, or nativeFile removed from both process and launch. **All 15 outcomes match the expected result.** The three healthy cases accept; all twelve adverses reject as `PROVENANCE_BLOCKED` with the intended command or bound-driver discriminator.

Independent result: `/tmp/r0016-third-20261111/work/independent_review/windows-core-candidate2/independent-command-binding.json`, 16,601 bytes, SHA256 `bb8ccec4a57207c488af2313ebc96162f184fcd1c75f4959d1dfde652718bae8`. Each row includes its exact retained fixture, launch fact, expected driver fact, and disposition. Complete synthetic files remain under the private packet's `validation/consumer-cases-core2/independent-*` directories.

Independent runner: `/tmp/r0016-third-20261111/work/independent_review/core2-command-binding-checks.py`, 4,193 bytes, SHA256 `7303a9adec14617692f94330877b676012d33e2d9f1a8e5eed71e5e649277f58`. It blocks both `subprocess.run` and `subprocess.Popen` while invoking the receipt APIs. Strings describing a wrong PowerShell command remain inert data.

## Fresh verification results

| Verification | Actual result | Evidence SHA256 |
| --- | --- | --- |
| `test_command_binding.py` in private packet | 72 tests passed, exit 0 | `a189c518d31d8aeea1607323d78afd9a3fc9dd885980a2927e772a5259fbeec5` |
| Static checker in private packet | 13 checks passed, exit 0 | `3c15aa443209da402fb11eb0ae67e92b4d06cb151f1b1d89eb01bb416d609dc6` |
| Preserved core1/core2 discriminator replay | Eight expected accept-to-reject transitions, exit 0 | `3f42bfd138c089cf8f07659276b87e8ca9dab6c7f8c4de2a3fe70eb780939ea2` |
| Additional independent receipt replay | Three healthy accepts and twelve adverse rejections, exit 0 | `bb8ccec4a57207c488af2313ebc96162f184fcd1c75f4959d1dfde652718bae8` |

The first three evidence files are `independent-tests.stderr.txt`, `independent-static.stdout.txt`, and `independent-transitions.stdout.txt` under `/tmp/r0016-third-20261111/work/independent_review/windows-core-candidate2`.

The 72-test run executes all 50 predecessor test methods plus 22 new methods once through the derived suite. It covers exact embedded-driver extraction, changed/ambiguous driver refusal, actual/baseline/guard/carrier command association, alternate or relative drivers, missing expected custody, changed bytes, additional arguments, missing/replayed spec bindings, explicit drains, all sixteen producer host associations, raw host/PID/nonce custody, inventory validity, independent baseline, and terminal deadlines. The static checks verify unchanged PowerShell bytes, exact driver corroboration, expected-driver wiring and custody inclusion, and intact frozen core1 and route1 histories. These are finite inert checks and do not execute the full native producer or any installer case.

## Final bounded disposition

No additional decision-changing counterexample was established in this repair review. WNR-01 and WNR-02 are closed for receiver SHA256 `c0f1dccae4a0e7f73867a6aa8c8d2ef8a76cd59e27e4edfcb6f4499d317e7978`. The disposition is **FINAL PASS for the command/driver repair and preserved receipt predicates**.

The standalone ten-control carrier and its separately reviewed route remain independent inputs and do not import this receiver. This PASS does not change the old core1 or route1 GAP reports. No native helper/wrapper, direct installer `-File`, normal/NoOpen survival, runtime containment, source-free native outcome, whole-contract, delivery, or closure credit is created. Native product cases relabeled: **zero**. Root alone may integrate the reviewed source and own any subsequently authorized execution and evidence receiving.
