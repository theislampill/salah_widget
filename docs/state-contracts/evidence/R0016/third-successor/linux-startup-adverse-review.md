# Linux startup diagnostic C1 — independent source review FINAL

## Disposition: NEEDS_REVISION

The exact two-file proposal preserves the existing containment policy and is bounded to source-free observations, but its acquisition predicate can accept absent or misbound syscall telemetry. This is a concrete evidence-validation gap in the proposed diagnostic, not a product or host-policy finding. No shared source was modified, no native test was run, and no archived code was executed.

## Frozen source packet

- Candidate manifest: `2799259261a0de7e03ea4de6f973b7c4304eda40fe412242f9130b5f78390f86`.
- Proposed probe, 14,587 bytes: `a30c87418780bdd842ace9c7a1e09b1e5afa09799b64a8467e8af1f0fd3dd81a`.
- Proposed workflow: `4e4d56dc8ba771b4a260a3bb58a4ff7d55b1398669ad292987ff8ffe1e2155e7`.
- Derived observer: `f77670dc2aa5fa9b0aa9c00b59d88965007c55caaf3e28845f7ff16e8f886928`.
- Base current fixture: `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00`.
- Reviewed namespace/lifetime/inventory support: `8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328`.
- Reviewed Ubuntu22 prerequisite helper: `adb7c47a6416b51bf96b6647e500bfba4e2d206a50a408a0e331f16d61ea9161`.

All manifest members and all four base inputs match their hashes; the base inputs also match the published `a80558ae97ac2697ec6727356928dd7a394eee60` Git blobs. The two proposed files, complete base inputs, declared scope, validation source, and manifest are retained under `candidate-1/` in this reviewer directory. A nonmanifest Python bytecode cache in the author scratch was not imported, copied into the review packet, or included in the two-file proposal.

## What the exact source preserves

The private observer is exactly the original prefix through the early `--sandbox-child` dispatch, with one raw-row expression expanded to record six syscall arguments, monotonic time, initial child PID, process stat and command-line bytes/hash, executable path, and readiness bytes at notification. Reversing that one expansion reproduces the original prefix byte-for-byte. The same six syscall names (`socket`, `socketpair`, `connect`, `sendto`, `sendmsg`, `sendmmsg`) and the same `DENIED_EPERM` response remain in place. The added observations do not authorize or continue any denied syscall. The later CLI and fixture/product dispatch are outside the derived prefix; the retained `positive_child` function definition is not called.

The probe imports the digest-pinned support module under a non-main name. It uses the original unshare command constructor, read-only host bind, owned writable fixture bind, cleared/set environment, process-local subreaper, pidfd-bound descendant cleanup, and complete two-pass inventories. No `sudo`, security policy mutation, host-root subject, PATH masking, cache clearing, or fallback to uncontained execution was introduced. The script launches only Bash builtins and a fixed source-free Python control.

The four cases differ explicitly: default environment without readiness, default with readiness, explicit namespace-correct USER/LOGNAME/SHELL with readiness, and explicit post-readiness UNIX/TCP/UDP plus outside/inside write controls. The USER/LOGNAME/SHELL comparison is a hypothesis test, not a fixture/product repair. Every raw event remains recorded and the script states that raw facts alone do not classify an event as startup or installer activity.

Subject execution has a 30-second monotonic deadline, followed by the unchanged five-second cleanup budget; captures use direct owned files with a one-MiB per-stream bound checked during polling. A naturally observed terminal, complete cleanup without signals/errors, full outside snapshot equality, empty stderr, and complete semantic output are required. The separate Ubuntu22 workflow retains read-only permissions, an exact-commit credential-free sparse checkout, pinned actions, a distinct concurrency group with cancellation disabled, a ten-minute job timeout, and always-run artifact retention. Prerequisite acquisition remains the reviewed signed-APT path.

## Blocking finding: semantic success is not joined to new telemetry

In `run_case`, `transportAttempts` is populated from the log or assigned an empty list if no log exists. The controlled Python stdout is then checked for three EPERM denials, outside-write denial, and the allowed owned write. Neither the raw transport log nor any of its PID, argument, executable, command-line, clock, or readiness fields is required by `semanticCaptureComplete` or `acquisitionComplete`.

Consequently, successful native stdout plus normal lifecycle facts can produce `SOURCE_FREE_OBSERVATION_ACQUIRED` even if the purpose-specific syscall observations are absent or belong to a different call/process/phase. A missing log remains explicitly `transportLog=null`, but its accompanying `transportAttempts=[]` is still admitted. This diagnostic must not treat that as an established zero-attempt observation or a proved positive telemetry control.

### Exact inert reproduction

`reproduce_c1_gap.py` isolates the exact candidate `run_case` AST and supplies reviewer-owned, inert dependencies. It never invokes a subprocess, namespace, shell, socket, or installer; it does not import received archive source. It supplies valid semantic stdout, ready-file bytes, natural terminal and cleanup facts, and stable inventories solely to test the acceptance predicate. All file writes occur below this reviewer directory.

| Supplied telemetry condition | C1 acquisitionComplete | C1 classification |
|---|---|---|
| Bound three-row control | true | SOURCE_FREE_OBSERVATION_ACQUIRED |
| Log missing, attempts empty | true | SOURCE_FREE_OBSERVATION_ACQUIRED |
| Wrong controlled PID | true | SOURCE_FREE_OBSERVATION_ACQUIRED |
| Wrong socket family argument | true | SOURCE_FREE_OBSERVATION_ACQUIRED |
| Wrong notification readiness nonce | true | SOURCE_FREE_OBSERVATION_ACQUIRED |

These are source-level counterexamples to C1's evidence predicate, not claims that those corruptions occurred on a native runner. Exact results are retained in `c1-gap-reproduction.json`.

## Minimal bounded correction

Add a pure telemetry predicate inside the existing semantic-acquisition gate. Require the controlled observations to join the control stdout PID to the recorded physical Python executable and exact control command line; require three ordered denied socket tuples for UNIX/stream, INET/stream, and INET/datagram, with six unsigned integer arguments and explicitly handled plain/CLOEXEC socket-type values. Require the initial child PID to match the independently captured Bash marker, the readiness bytes to match that Bash PID plus the exact nonce, and notification timestamps to fall inside the recorded launch-to-first-terminal interval. Verify the retained command-line and stat byte hashes and PID; recheck the physical Python binding after the case.

Keep every raw record. Select controlled records using executable plus PID, because Bash may exec another process without changing PID; a PID-only filter could conflate earlier Bash startup calls with Python control calls. Extra same-process Python records should cause an explicit evidence gap unless separately explained by additional bounded proof. Do not erase or automatically interpret extra Bash rows. Missing or malformed required telemetry must prevent acquisitionComplete.

No change to the six deny rules, EPERM response, containment construction, original product fixture, host policy, or original Linux22 failed evidence is needed for this correction. Native source-free acquisition remains a separate future observation after review of the revised frozen packet.

## Original failure context

The independent minimal original Linux22 receipt is in sibling `linux22-native/REPORT.FINAL.md`. The original kernel control succeeds, then missing-readiness is blocked by two retained socket denials without arguments or phase metadata. That evidence supports acquiring richer raw facts; it does not establish that the calls are AF_UNIX, NSS, or Bash startup activity. No such attribution is made here.

`c1-verification.json` records 23 source/data consistency checks. This report is a bounded source review, not a formal governor verdict, dispatch authorization, readiness declaration, or closure.
