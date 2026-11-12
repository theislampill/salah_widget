# Windows reconstruction candidate 1 — independent receiver review

State: **FINAL**. Disposition: **GAP-REVISE for the NEW receiver**.

This ordinary independent review covers receipt admission and command-input binding. It does not authorize publication, native dispatch, installer acceptance or lifecycle changes. The standalone source-free carrier has a separate bounded report; its result must not be turned into an overall Windows PASS.

Requested model: inherited parent, no override. Actual model: host-declared GPT-6 Astra Pro; provider deployment identifier unavailable. `authoring_context_reuse: no`. This reviewer did not author the Windows producer, window support, receiver or carrier. Actual files were inspected before the current author's report. No PowerShell, installer, native child or network process was executed. Python checks operated on a private copy and inert synthetic records only.

## Exact packet and provenance

Original packet: `/tmp/r0016-third-20261111/work/windows_recovery/frozen-candidate-1`.

Manifest SHA256: `08d7be4b936d269589efe597bb0dfbd3c707e6a0d1434a8fcfdd821b34e33923`.

All **25 payloads / 398418 bytes** independently match the manifest. The received private copy is `/tmp/r0016-third-20261111/work/independent_review/windows-core-candidate1/packet`. Receipt SHA256: `92fe13db6db50eed1d40139adb094475b6b9102da03831fbe2481310e3bf1e03`.

| File | SHA256 | Status |
| --- | --- | --- |
| Proposed install-preview-native-controls.py | `851cf29917ed0ced30e7ebd1195f49de430b6f5bdf02d7fbc1643ce8af9889df` | NEW receiver under review |
| Recovered base receiver | `795f712345e4b1dad77243f28a59146bfb19bb38ddd2b74a80adec7fc26a55a2` | Exact recovered in-progress bytes, not the missing final core3 receiver |
| install-preview.ps1 | `e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916` | Exact recovered producer |
| install-preview-window.ps1 | `05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83` | Exact recovered support |
| install-preview-acquire-timed.ps1 | `b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1` | Exact recovered acquisition library |
| Author report | `b6e8220e3dafb17121604749a7ac60683385dbb5d97e1ab305b0aee008014c35` | Handoff evidence, not independent qualification |

Each declared recovered input was independently compared with its `input-manifest.json` source path. Both base copies and all unchanged proposed PowerShell inputs match those originals exactly.

Historical G0010 adverse evidence remains at `recovered-G0010/second-successor/product-review/windows-core-candidate-1`. Its FINAL GAP review has SHA256 `8b0433523810046ef938eb0256e76d26ee1803dafc73a99c36834e3185f8a061`, and its adverse-results JSON has SHA256 `9a75153ef2dce26f3132dc9cd5894603e937f4c6dfb446af7d8c28eda9f960ec`. No historical failed review or missing final-receiver provenance was overwritten or promoted.

## Checks that succeeded

Private-copy unittest discovery exited 0 with 73 test-method executions: the reconstructed receiver class executes 50 methods, including 23 inherited methods, and discovery also executes the 23 base methods again. This is not 73 distinct product cases. The methods include checks for all sixteen healthy/mutant host positions. The 16 pure static checks also pass, and all six recovered-versus-NEW comparisons reproduce the intended transition from false acceptance to rejection.

The resulting static report remains SHA256 `28b15e085f4dbf74f6836fa06d5abf22124fdf3d3ab2b8ef37fd000452f29251`; the fresh comparison report remains SHA256 `4d77223dc42a6c0182a4481e2239fa93a92a01b762d592b076787d053023d56f`. These reruns are Python-only; there is no PowerShell parse or native execution credit.

The NEW receiver correctly requires explicit Boolean drain completion for both actual and baseline v2 records. It binds their raw launch hosts to the row's absolute commandHost and, at preflight, to the one host derived from all sixteen healthy/mutant observations. Carrier windows and guard launch records use that same host. The historical v1 path retains omitted-drain compatibility and full-lifecycle semantics; new window fields cannot opt v1 into v2. The retained root/kind/hash/length, baseline association and late-terminal controls continue to pass their tests.

## WNR-01 — raw launch arguments are not bound to the claimed file invocation

Priority: **P2, qualification-instrument defect**. Confidence: **high, exact-code inert reproduction**.

Starting from an otherwise valid synthetic v2 case, the reviewer first supplied coherent `-NoProfile -File "<driver>"` arguments on both actual and baseline raw launch records. That healthy companion is accepted. Changing either raw launch's `arguments` to the following, while preserving all other correct facts and recomputing the raw file's SHA256/length, is also accepted:

```text
-NoProfile -Command "Write-Output wrong-entry"
```

Deleting `arguments` entirely is accepted as well. The same mismatched or missing arguments are accepted by `verify_guard_launch`. The held-window verifier and guard verifier do not inspect this field, and preflight has no later argument check. Raw bytes are authenticated, but they can explicitly describe a different PowerShell invocation from the driver invocation being credited.

The direct reproductions exercise the actual `verify_case_files` and `verify_guard_launch` functions; they do not claim a fabricated full core receipt or any actual PowerShell invocation. Source inspection establishes that preflight calls these functions without a subsequent raw-arguments check.

Fix requirement: v2 command admission must require and validate the raw invocation arguments against the declared driver and supported invocation shape, for actual, baseline, six carrier windows and four guard launches. Preserve v1 compatibility through its explicit version branch. Retain a healthy producer-shaped record plus missing/mismatched arguments negatives.

## WNR-02 — absent driver fields can satisfy held-window equality

Priority: **P2, qualification-instrument defect**. Confidence: **high, exact-code inert reproduction**.

Deleting `nativeFile` from both the process projection and its raw launch JSON is accepted for both actual and baseline cases. The current comparison becomes `None == None`; unlike the guard-launch verifier, the held-window verifier does not also require a nonempty driver string. Therefore the receiver can admit a held-window proof with no native script input identity at all.

Fix requirement: require the actual driver path to be present, well-typed, owned/bound as appropriate, and consistent across process, raw launch and the validated invocation arguments. Equality of two missing fields must not establish input identity. Include actual and baseline healthy companions and missing-on-one/both-sides negatives.

## Exact independent counterexamples

Reviewer result: `/tmp/r0016-third-20261111/work/independent_review/windows-core-candidate1/independent-command-binding.json`, SHA256 `c5390497ca6a03c782dcafab529c153b8db7ad703a4c2a278661d7ebe5bcea41`.

Nine checks were performed: one valid companion accepted as expected, and eight invalid variants incorrectly accepted. Each exact synthetic fixture and an `independent-result.json` sidecar are retained under the private copy's `validation/consumer-cases-new-reconstruction/independent-*` directories. Raw launch hashes were kept consistent with the modified contents, so these findings concern semantic admission rather than stale hashes. Process-launch functions were replaced with rejecting guards during this replay; none was called.

## Return to root

The NEW receiver remains blocked for the claimed v2 command-input admission until the two findings are repaired and independently replayed. No production installer defect is asserted. The exact recovered PowerShell inputs and the NEW source-free carrier are assessed separately; the receiver is not an input to that carrier's native workflow. Original v1 evidence, original adverse reviews, native product qualification, direct -File behavior, normal/NoOpen survival and all wider R0016 obligations remain separate.
