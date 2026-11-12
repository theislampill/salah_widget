# Independent source-free direct-driver C2 re-review

**FINAL disposition: PASS — bounded code/receiver review of these exact source-free diagnostic bytes.** DDRV01 and DDRV02 are resolved. Native qualification remains unacquired; this review grants no product acceptance, dispatch, publication, integration or lifecycle authority.

## Exact packet and scope

Reviewed author packet: `/tmp/r0016-third-20261111/work/windows_recovery/direct2/frozen-driver-diagnostic-2`.

Manifest SHA256 `5cf40d9285deca5b8e2d2a82e07abc01078dd448e3bfe4f4a629f9355fc8138d`; all37 payload files/1,273,234bytes and the exact inventory were independently verified. Controller is47,331bytes, SHA256 `e192018d2379792cdd1fd73e566b0d50057600b1d25e70430458fee56bbe9d76`. The author report is SHA256 `9539cfc447c25248a1151b2f13fab5cadd2014ba8e8ed34e0b8ba6fca2ec2337`.

The independent raw diff and AST comparison confirm that `validate_direct_neutral` is the only production function changed. All seven other native input files are byte-identical to C1. The change requires actual process-start evidence, the four owned cleanup step identities, and the exact direct-file capture protocol. The actual acquisition and cleanup functions already emit those fields; they did not change. The only supplied healthy synthetic fixture correction adds the already-emitted capture protocol field that its old synthetic receipt omitted.

Requested model: inherited parent model, no override. Actual host-reported model: GPT-6 Astra Pro; no finer backend attestation. **Implementation authoring_context_reuse: no. Prior independent review continuity: yes.** This reviewer found DDRV01/02 and recommended the predicate requirements; the Windows author wrote and froze C2. This is transparent same-reviewer repair verification, not a claim of a fresh reviewer with no prior findings. The separate core/normal route authored by this reviewer is outside this review.

## Independent original-fixture replay

The reviewer reused the original retained raw fixture from `direct-driver-review-1`, not the author's new repair summary. The original adverse JSON remains immutable. The replay reconstructed the pair from that fixture's actual association/spec/prepared inventory files and called the real C1 and C2 predicates. The healthy baseline and cleanup adverses received the truthful capture-protocol field already emitted by the C1 production acquirer, so the cleanup rejection could not be attributed merely to a missing protocol field. All original raw gate, capture and probe files remained unchanged.

| Case | C1 | C2 | Meaning |
|---|---|---|---|
| Healthy direct receipt with actual capture protocol | Accept | Accept | Required healthy behavior retained |
| Original DDRV01: processStarted=false plus irrelevant cleanup step | Accept | Reject | Contradictory process/cleanup record rejected |
| DDRV01 step identity check isolated with processStarted=true | Accept | Reject | Required owned poll/wait/capture steps enforced |
| Original DDRV02: redirected pipes/never-drained capture claim | Accept | Reject | Exact direct-file protocol enforced |
| Native direct exit changed to integer17 | Reject | Reject | Existing exact terminal discrimination retained |

All10 predicate evaluations completed with those expected results. C2's three rejection reasons respectively identify incomplete genuine cleanup, missing independent owned cleanup steps, and wrong capture protocol/terminal confirmation. These decisions are preserved with full receipts in `independent-replay.json`, and the executable inert replay is `replay_original_adverses.py`.

Original C1 review remains FINAL GAP-REVISE at `/tmp/r0016-third-20261111/work/independent_review/direct-driver-review-1/frozen-review-1`. Its report SHA256 is `5d84d9c85831492365a174dd623cc083972656ab3ba8e8aacf18b19c18cf0255`, manifest `0bdd50cee634900a0c013ef50513d5ab816b4682bfc67ac355f9c99c30622302`, and complete raw independent fixture archive SHA256 `9385874c1153c2aac670f473778c0a99fc961209929539bb0eebd2ab730f0b41`. No historical adverse disposition was overwritten or relabeled.

## Additional executed checks

The supplied repair replay was also run in a separate writable copy of C2 and passed its10 old/new predicate evaluations. It executes the existing72 inert receiver controls, which passed19 expected accepts and53 expected rejects. The21 static checks passed, including the actual Python non-Windows guard returning the blocked result before any native acquisition. No PowerShell parser/runtime or installer was run. The original seven native dependencies and all C1/C2 source packet payloads were reverified unchanged after the work. The previously reviewed cleanup repair was not redundantly re-executed because its exact bytes are unchanged and this delta affects only the direct-neutral receiver.

## What this PASS covers

C2 repairs both concrete C1 receiver defects without changing source-free case generation, native driver semantics, typed argv, source/probe/host association, original Utility readiness, held before/after gates, cleanup acquisition or the input relationship. The bounded positive assessment in the C1 independent report therefore applies to these unchanged functions with the two direct-neutral omissions resolved. No additional decision-changing defect was found in this narrow re-review.

This diagnostic still runs only its fixed neutral/source-semantic/effect controls. It accepts no installer source argument. Its original genuine direct neutral entry and held entry remain separate; source semantic exit is not replaced by wrapper exit. The whole healthy held interval remains unchanged across its complete six-role observations. Native startup and postexit differences remain retained. No prepared-input, timestamp, filename or profile-cache exception is introduced.

The root must provide the separately reviewed outer native route: exact eight input hashes, selected host/runtime binding, owned allowlisted environment before selected PowerShell startup, bounded Job lifetime and full raw evidence preservation. A Job Object is not filesystem or network containment. Actual native PowerShell parsing, startup/ACK behavior, exit semantics, source-method denial and actual child-read equivalence remain future evidence. The unfinished product input mapping, original normal/NoOpen confinement, historical317 and R13 source change remain outside this PASS.

## Exact native input set

| Native file | Bytes | SHA256 |
|---|---:|---|
| `tests/install-entry-composition-support.py` | 37442 | `4600bac181dcac5fe7f72467c6018800666284d7087cf98f8b9bf5a449910821` |
| `tests/install-entry-coverage-support.py` | 14701 | `52a268b0de8c6055f8265faa7bdef115a78ba29fba2b4f008aba43be6b793c4a` |
| `tests/install-entry-diagnostic-shadow.psm1` | 5710 | `5bc1cb8b88c6c873a295f664304968d7a859c0f322223b8b6bb8b15798f67663` |
| `tests/install-entry-driver-diagnostic.py` | 47331 | `e192018d2379792cdd1fd73e566b0d50057600b1d25e70430458fee56bbe9d76` |
| `tests/install-entry-held.ps1` | 7729 | `a3ccac853a6108a2ed860a66f6e8bd6547efd3cc06c3626283959b3126997ae6` |
| `tests/install-entry-input-probe.ps1` | 12493 | `f4c871734c72a71c04423a3fcfc1c4c9a2286da7683d09a1eb6ffeefb73c2bf0` |
| `tests/install-preview-window.ps1` | 13117 | `05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83` |
| `tests/install-preview.ps1` | 57909 | `e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916` |

## Authority and completion

All authorized review work is complete. Work outside the reviewer's scratch directory was read-only. No shared source, Git, remote service, permissions, native job or lifecycle state was changed. Root retains the sole publication/dispatch authority and must independently receive any future native artifact. This report is a bounded independent assessment of frozen C2, not permission to bypass that route or claim product/native acceptance.
