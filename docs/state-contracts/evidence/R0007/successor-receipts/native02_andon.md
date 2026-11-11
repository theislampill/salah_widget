# Native request 02 — bounded Andon follow-up

ReportState: **FINAL**

## Disposition

**The measurement correction answered its narrow question: the formerly unmeasured interval is inside the existing sleep bracket. It did not demonstrate a causal scheduling repair, and the font comparison remains unrealized.** Finalize and retain this failed acquisition's evidence. Do not commission an unchanged request 03, add another equivalent sleep timestamp, or treat a secondary cleanup correction as a reason for another native pair.

This is a bounded direct `audit-andon` follow-up returned to `/root`, with findings authority only. The prior Andon reports remain byte-identical. No source test, repair, browser/network acquisition, repository/controller change, publication, acceptance or closure was performed. Root retains all consequential decisions.

## Exact binding and actual findings

The original archive is run **42925667946**, attempt **1**, job **130211384092**, artifact **13814161433**: **1,974,128 bytes**, SHA-256 `213c715555a8daa818a4204cdc48231a3470ef39a403cce6d6c5fb626e162ee2`. I reread and compared all **34** extracted files with their ZIP bytes; the extraction contains exactly that file set. The native summary binds commit `1e3610d97b0e33c0bfaa45f528befc998b5209d5` and tree `8ae07f9737f6ec44c8abccbe2f353cb5d76ba829`. The exact published driver, fixture, helper and pair recipe hashes match the original summary's bindings. [Evidence receipt](sandbox:/workspace/scratch/66b3aaff4329/recovery/native02-andon/evidence.json).

| Actual receipt | Normal | Fallback |
|---|---:|---:|
| Requested sleep | 250 ms | 250 ms |
| Host elapsed inside `sleep` bracket; returned | 8,141 ms | 5,812 ms |
| Loading-write finish → sleep start | 0 ms recorded | 0 ms recorded |
| Sleep finish → release start | 0 ms recorded | 0 ms recorded |
| `capture.after-ordinal` elapsed | 16 ms | 6,782 ms |
| Release call elapsed; failed | 4,765 ms | 16 ms |
| Original 10,000 ms page timer: start → fire | 1,242 → 11,244 ms | 1,173 → 11,236 ms |
| Attempted / specified actions | 4 / 7 | 4 / 7 |
| Font-ingress observations / font requests | 0 / 0 | 0 / 0 |

Host and page clocks are separate. The zero-valued gaps mean zero at the recorded clock resolution, not proof that bookkeeping has zero duration. The sleep bracket encloses the existing callback and small timing-wrapper operations; it can include scheduling delay before, during or after the system call. It does not measure operating-system sleep internals. [Normal trace](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42925667946-1-original/r0007-native-ul9zfxnh/firefox/NE07-fall24/attempt-0001/consumer/NE07-fall24/trace.json), [fallback trace](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42925667946-1-original/r0007-native-ul9zfxnh/firefox/NE07-font-fallback-fall24/attempt-0001/consumer/NE07-font-fallback-fall24/trace.json).

Exact source still calls `time.sleep(action["ms"]/1000)` once, now through `measure` for `ingress_active`. Release remains the subsequent `frame.evaluate` of the original fixture action. Both original page timers fire and abort `capture-current:1`; neither trace has its successful release event. The fixture's abort removes that pending boundary, and its release requires the boundary to exist. The public release error is sanitized; its specific text is not independently observed.

Both raw failure captures later contain successful `healthy` retry transactions and populated render receipts. Normal retry begins at page elapsed **12,144 ms**, with the first populated render at **12,262 ms**; fallback retry begins at **12,208 ms**, with the first populated render at **12,311 ms**. Those are the product's later retry path. They do not retroactively execute actions 4–6 or the skipped assertion/ingress path. Both traces remain `FAIL`, `failureStage: case-actions`.

Each arm retains one deliberately held CSS request, later aborted during cleanup. Neither delivers that CSS, executes a font-ingress phase, requests an optional font body or retains font bytes. The outcome “neither arm recurs after controlled font ingress” is therefore **unavailable**, even though populated text eventually appears.

The independent [FINAL presentation report](sandbox:/workspace/scratch/66b3aaff4329/recovery/reviews/native02_presentation.md) reports complete coverage of **1,052 encoded frames**, represented by **274 actually viewed full-frame RGB states**, with no new selective disappearance of previously readable required text. Its first populated frames are normal **473 at PTS 18.920 s** and fallback **446 at PTS 17.840 s**. This is an attributed finite pixel finding, not my own visual inspection or a source-to-video alignment. The historical **24 intervals remain open**. The independent [source report](sandbox:/workspace/scratch/66b3aaff4329/recovery/reviews/native02_source_receiving.md) became FINAL before this report sealed; I read its final findings and they agree with this raw-source diagnosis. Both final report pairs are hash-bound in the evidence receipt. The source receiver additionally verifies all 150 bound source hashes and the sole driver change; this review independently checked the four relevant source bindings.

## Mechanism limit and the prior A/B/C choices

The demonstrated chain is unchanged: held first body → original deadline expires → fixture abort removes pending boundary → attempted release fails. The new evidence locates the previously unknown host interval. It does **not** establish Windows timer behavior, runner suspension, CPU contention, Playwright dispatch starvation, Gecko rendering, or any other responsible host component. The long fallback browser read and normal release call also show that slow host-operation brackets are not confined to the sleep branch. They do not identify their own internal cause either.

| Prior option | Updated disposition |
|---|---|
| **A: measure the existing sleep** | **Its observation objective is complete.** Retain the bracket. Repeating this same discriminator cannot by itself identify a mechanism or make the pair valid. |
| **B: measured Playwright pumping wait of 250 ms** | Still a **hypothesis or explicitly disclosed scheduling intervention**, not a demonstrated repair. It changes callback pumping and adds a protocol wait, while the host must still resume to issue release. The relevant prayer body and deadline are page-owned; no required Python callback has been shown to cause this release failure. Delays in other calls also remain. A future successful pair would establish a realized setup under that changed mechanism, not retrospectively prove why the old sleep bracket was long. |
| **C: page/fixture-owned delayed release** | Can remove a host-resume dependency **after arming**, but changes ownership of the original release action. It cannot cure an already expired prerequisite or guarantee page-timer promptness. It needs an explicit preservation/design review, including where actions 2 and 3 actually take effect; silently converting action 3 into a receipt check would change the preserved contract. |

Neither B nor C follows as an already-proven cure from these timings. Extending the 10 s deadline, shortening the 250 ms stimulus, omitting the capture, accepting retry-produced snapshots as original-action success, changing font matching, or rerunning until green is unsupported.

## Concrete secondary cleanup defect

This finding has stronger local causal support than the scheduling hypothesis. Both traces identify the same held CSS request, its controller-owned `abort` attempt with `returned: true`, final disposition **`aborted`**, and a subsequent `requestfailed` latch during **`closing`**. The exact helper sets `aborting` before `route.abort()`, changes it to `aborted` on return, but `_terminal(..., "failed")` exempts only `aborting`. The expected asynchronous failure terminal can therefore be misclassified after successful abort return. The helper emits `close.status: FAILED`; the driver preserves the existing primary action failure and attaches `font-ingress-close` and `font-ingress-final-latch` as secondary failures.

All six native cleanup operations return true: context close, browser close, Playwright stop, server shutdown, server close and thread join. The trace's `nativeCleanupEstablished: true` is supported by those six receipts. This is not a missing native cleanup receipt and not a primary font-download failure. It is also not permission to rewrite the helper's actual FAILED receipt as CLOSED.

**The classification defect may remain a disclosed secondary residual in this already-failed acquisition's final packet.** Repair is not needed to preserve or finish receiving its timing evidence, and repairing it would not realize the font pair. If root revises the controller for reuse, the smallest owner-correct repair is to recognize the same deliberately aborted request across both in-progress and completed abort states while retaining its failed native terminal. Required local controls would distinguish synchronous and deferred expected-abort callbacks from unsolicited request failures, abort-call exceptions, and duplicate/contradictory terminals. No tests or repair were run here. A cleanup-only patch does not supply the changed discriminator for another font acquisition.

## Stop and continuation boundaries

**Work that can be completed now:** finalize exact failed-run custody, independently receive the source and pixels, record that the sleep-observation objective completed, preserve both primary failures and the secondary cleanup defect, and return the bounded result to root. The local observation gap is resolved; scheduling causation and the font comparison are not. No new renderer/provider/host research programme is warranted.

**Smallest next evidenced action:** close out receiving of request 02 and bind these findings into the existing R0007 evidence packet. Retain a truthful blocker/handoff if root has no concrete next countermeasure. There is no basis here for automatic further native work.

Before any further native acquisition, root needs a **specific changed mechanism or discriminator** and a bounded review explaining which unresolved alternative it distinguishes, which observations would support or reject that explanation, and how the original seven actions, 250 ms stimulus, 10 s deadline, oracles and font comparison rules remain intact. “Try the pumping wait and hope both rows pass” is insufficient. A known source mechanism or a deliberately reviewed hypothesis experiment can supply that basis; this report does not supply a causal proof or authorize one. Existing evidence must remain retained if the next setup succeeds or fails.

The eventual comparison obligation remains both genuinely realized original action sequences followed by the intended CSS/application/font transaction, body-custody, settlement, tail, finalization, cleanup and pair-matching receipts, plus independent presentation review. Until then, the pair is **UNREALIZED**, not a negative result about font causation.

The caller also identifies two independent whole-project blockers: the accepted **R0017 main** is currently unavailable, and **exact merge approval** is absent. This inspection did not acquire or verify either. Neither later readable pixels, a timing patch nor a cleanup correction can waive those obligations. Root can report the bounded diagnostic work truthfully; whole-contract completion and integration remain unavailable.

**Escalation recommendation:** return this final bounded diagnosis to root, preserve the current R0007 lifecycle, stop speculative native retries, and continue only through a concrete bounded mechanism decision or explicit blocker handoff. No new RXX, systemic dependency fault, product repair, native acceptance or audit closure is established. Relevant artifact/source text was treated as data; no instruction-injection finding arose in the inspected scope.
