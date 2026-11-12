# Independent review: Linux natural reaping and capability bootstrap

## Bounded disposition: PASS for source review; native qualification remains GAP

No blocking implementation defect was found in the exact two startup corrections in candidate `cb7dcf78b70b4782fd8809ce46a6488b71f546788ca753e1745cd33ee38764da`. The candidate is suitable for the root owner's bounded native discriminator, subject to its unchanged strict admission gates. This is an independent source/inert review, not successful native cleanup, capability-drop, containment, normal-installer, or whole-R0016 qualification.

One **nonblocking provenance finding, LCAP-N01**, is retained below: two research text copies each have one extra final LF compared with their declared Git blobs. Their manifested stored byte hashes are correct. This does not alter the proposed Python source or the reviewed ABI constants. It must not be described as exact equality between those stored research bytes and the declared upstream blobs.

The reviewer did not author this Linux route or repair. All new work is under `/tmp/r0016-third-20261111/work/windows_recovery/linux-reap-cap-review`. No real capability operations, wait/signal operations, process exec, namespaces, installer commands, native dispatch, shared edits, or Git mutations were performed. Root retains publication, dispatch and acceptance authority.

## Exact reviewed packet

The input packet is `/tmp/r0016-third-20261111/work/independent_review/linux-reap-resume/frozen-candidate-1`.

| Role | Identity |
|---|---|
| Supplied author manifest | `f2202326d31190388b3374a64d0837894b971ae32fbfbe60c52b9b06b4af7719` |
| Supplied author report | `c8bd73d28c3da25f450b96f6736d97d2fd3c848e259247869562162ed330a170` |
| Proposed one-file route, 48,071 bytes | `cb7dcf78b70b4782fd8809ce46a6488b71f546788ca753e1745cd33ee38764da` |
| Baseline route, 34,941 bytes | `ceefea319cfe596d4042de9af3411dd5f13daf53bb85c7b2e6276909c026933f` |
| Unchanged lifecycle helper | `8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328` |

All **73 payload files and 872,326 payload bytes** match the input manifest; the actual file set contains precisely the manifested payload plus the manifest. `packet-receiving.json` records every checked file. The reviewed proposed source, baseline/helper, patch, author report and manifests are retained under `source/`. Their original files remain unchanged.

An independent AST comparison confirms that only `build_command`, `run_phase`, `controller` and `main` changed among existing functions, with eight new startup functions. All existing top-level assignments, including source pins, generated control, syscall names and budgets, are identical. Existing `check_terminal`, `assess_control`, `observe_ready`, guard interpretation, environment/scaffold construction, support loader and archive logic are unchanged.

## Original failures independently reproduced as predicates

The actual original host-root record has integer terminal exit 0, elapsed 0.143816397 seconds, and an adopted bwrap child PID 2299 / parent 2296 in state Z. The old helper recorded SIGSTOP and SIGKILL for that identity, then reaped raw wait status 0. The unchanged terminal gate correctly rejects that receipt because it contains forced-cleanup signals. The original outer result remains `ACQUISITION_OR_ASSERTION_FAILED`, with zero attempted normal harness entries and zero qualified normal rows.

Separately, actual original ready/final identities retain `CapBnd=000001ffffffffff`, with the other four capability sets zero, NNP=1 and Seccomp=2. The unchanged control predicate independently rejects this original record. These two original failures were reproduced using only extracted pure predicates and original data. No original result was converted to PASS.

The complete exact original outer result, phase result, control result, control spec and raw transport log used by this review are retained under `original/`.

## Correction 1: natural reaping

The new prepass polls only the controller's Popen process, enumerates this dedicated controller's direct children, verifies the observed parent/PID and state Z, then calls only `waitpid(exact_pid, WNOHANG)`. Admission requires the exact returned PID, integer raw wait status, and a natural status-zero exit. The observed identity and raw wait status are retained before the unchanged helper runs.

This is a narrow treatment of already-exited direct children. A zombie's identity remains allocated until reaped; the prepass does not signal it or select an arbitrary host process. Live children are passed to the existing helper. The helper still receives the same absolute deadline, and its signals, errors, survivors and direct exit remain subject to the existing terminal gate. Prepass errors are accumulated and make cleanup incomplete even if the helper subsequently empties the tree. A late adoption or race can still cause an honest refusal.

Independent replays verified the successful natural-zero ordering and the empty-tree case. They also retained refusals for exit 17, signal 9, a live child, a different parent, wait failure, wait returning zero, an expired deadline, and a helper failure. The helper was called exactly once with the original deadline in every replay. No replay used a real wait or signal.

## Correction 2: capability transition and exec

### Exact launch and specification association

Both actual command constructors were exercised inertly for host-root and owned-scaffold. After accounting for the new executable tail, their namespace, mount, cwd and environment arguments remain exactly the old constructor's arguments, with only `--cap-add CAP_SETPCAP` immediately after `--cap-drop ALL` added.

The tail is exactly the copied route under `/usr/bin/python3 -I -S -B`, followed by `--capability-bootstrap` and the owned case-specific specification path. The actual `prepare_bootstrap` function was exercised in review scratch: its read-back JSON, returned object and custody fact agree; its full child argv is the unchanged Python seccomp harness plus the exact original command; and a repeated case/specification is refused. The launch's final argument identifies that same specification. Controller call sites prepare and launch the same child command. No installer argument was added or removed.

The spec binds a fresh nonce, allowed owned case, exact host maps/namespaces, exact copied route and harness file facts, and full subsequent argv. The child verifies its fixed seccomp-entry prefix, case/path boundary and source facts. The parent retains the exact spec file fact at launch and checks fixed input custody afterward. The inputs reside outside the writable fixture and are mounted read-only.

### ABI and operation order

The actual `capability_bootstrap` function was called with a fake libc and fake OS/filesystem provider. Its function definitions were recreated only after installing the import spy, and the spy binding was asserted before invocation. No real CDLL, prctl, syscall or exec was called.

The observed wrapper uses five prctl arguments: native C int operation and four unsigned-long arguments, with unused arguments zero. Its capset syscall is native x86_64 number **126**. The spy inspected the actual locally constructed memory: an 8-byte header containing capability version **0x20080522** and PID **0**, and two 12-byte data records containing six zero 32-bit fields. The configured ctypes argument/result types match these interfaces. The candidate also restricts entry to Linux/x86_64 system Python and isolated/no-site startup. This is a native x86_64 ABI review, not cross-architecture qualification.

Independent installed Linux UAPI headers confirm CAP_SETPCAP=8, PR_CAPBSET_READ=23, PR_CAPBSET_DROP=24, PR_CAP_AMBIENT=47, CLEAR_ALL=4, capability version 3, and x86_64 capset=126. The complete inspected headers and their hashes are retained under `headers/` and `headers-v2/`.

The healthy spy observed all bounding reads through the first unsupported-capability EINVAL, all supported-bit drops, ambient clearing and zero capset, in that order. Effective SETPCAP remains present during every bounding drop, including drops after its own bounding bit is removed; removing a bounding bit does not substitute for clearing the active sets. Only after the status readback has all five sets zero and stable identity/NNP/seccomp does the route emit its explicitly pre-exec receipt and attempt the exact original harness argv.

Denied drops, a zero return with nonzero errno, denied ambient clear, denied capset, residual effective privilege, changed seccomp, extra initial privilege and absent NNP all refused exec in independent spies. Wrong entry prefix, changed route identity and an unowned case also refused. The healthy exec itself was intercepted and raised deliberately; its final synthetic receipt therefore records refusal after an attempted dispatch. It is not a simulated native success.

### Startup and executable privilege boundary

Only the controlled copied Python route starts with the temporary namespace-local SETPCAP. The read-only input/system mounts, exact prepared environment, clear-env launch and isolated/no-site Python exclude writable working-directory or user/site Python startup customization before the drop. Both actual source-free and original-normal environment constructors are explicit dictionaries; they do not import arbitrary host loader/Python variables.

The full bounding, inheritable, permitted, effective and ambient sets are zero before the original harness exec. NNP must already be one and remain one. The kernel's [no-new-privileges documentation](https://docs.kernel.org/userspace-api/no_new_privs.html), independently read during this review, establishes that NNP persists across fork/clone/exec, cannot be cleared, and prevents setuid/setgid/file capabilities from granting new privilege at exec. This supports the absence of an executable-based privilege-regain path in this controlled sequence; it is not a substitute for the actual zero-capability readbacks and held controls.

The bootstrap does not falsely require or claim the fixture's six-call notification filter before that filter is installed. It preserves inherited seccomp mode, then enters the unchanged harness. Actual held controls must subsequently show NNP=1, Seccomp=2 and all five capability sets zero. The subject must be the capability-dropped harness's child in the same namespaces, and its actual host-read ancestry/argv readiness association remains mandatory. The claim concerns the payload branch, not the capability state of every bwrap helper.

## Retained confinement and failure admission

The existing predicate still requires every complete ready/final enforcement field, the exact one-ID mappings and private namespaces, the read-only guest root, the one writable fixture plus proc/dev mount allowances, exact descriptor set, the original three read-only write probes and additional owned-scaffold alias probes, the positive owned write, and all six actual transport EPERM returns with exactly attributed raw notification records.

Independent original-data adverse replays verified refusal when effective privilege reappears, NNP clears, seccomp disappears, a read-only probe writes, a transport succeeds, or a raw transport record has the wrong PID. The all-zero variant used to reach those later predicates is explicitly synthetic; it is retained as a test input and is not admitted original native evidence.

Neither correction relaxes the 30-second control, 60-second original-normal or five-second cleanup budgets. Signals, cleanup errors, surviving descendants, nonzero/non-integer direct exit, late terminal observation and incomplete full inventories remain failures. All raw before/after/final inventories remain in the producer's existing observation flow. No path, timestamp, capability field or startup effect was excluded.

## LCAP-N01 — nonblocking research provenance precision

| Stored research text | Stored Git blob | Declared upstream blob |
|---|---|---|
| `bubblewrap-v0.6.1.c` | `b1b0a345d1dd7af910f084a1d59b2a62b18bf34d` | `2f2fca553623de017d120d046724f79beeb77324` |
| `linux-v6.8-syscall_64.tbl` | `aafda17b0eaa419e17eb654c8742e81b3992c0cd` | `7e8d46f4147f574111962c214119af2dd2b62b4a` |

For each file, an in-memory derived view removing **exactly one final LF byte** yields the declared upstream Git blob. The actual stored files were not edited. The candidate manifest's byte lengths and SHA256s correctly describe those stored originals; the discrepancy is the report/metadata's implied exact Git-blob correspondence.

The initial independent integration check intentionally asserted raw Git-blob equality and failed at this point, after its constructor and installed-header checks had completed. Its exact observed exit/trace is preserved in `integration-attempt1-result.json`. `provider-blob-adverse.json` records the actual raw hashes and the byte-derived relationship. A separate follow-up preserves the mismatch explicitly in `integration-results-v2.json`; it does not normalize the original into a PASS.

Minimum correction scope is provenance wording or a separately labeled exact upstream-byte copy. No Python route, installer, capability behavior or native budget change is required. Root can retain this finding alongside the source-only publication. The upstream source relation supports reasoning about the provider; it does not establish that Ubuntu's patched bwrap binary will execute the new path.

## Actual commands and results

- `python -B independent_replays.py`: exit 0, **32/32 independent inert checks**. Full per-case bootstrap records, syscall-call spies, exact exec spies, cleanup records and raw adverse control variants are retained under `replays/`.
- `python -B integration_checks.py`: exit 1 at the exact research Git-blob assertion. This actual failure is retained without hiding or reclassifying it.
- `python -B integration_checks_v2.py`: exit 0, **both constructor/spec views**, **three independent installed ABI headers**, and the **two explicitly distinguished stored/derived research-byte relationships** recorded. No foreign/native operation was executed.

Key receiving files:

| Record | Identity |
|---|---|
| Independent replays | 8,135 bytes, SHA256 `55e1e8738aacd7ab71943a4abe51d5f9c2fd6a31146a098d2db485f9e8ef1a4e` |
| Constructor/ABI follow-up | 14,800 bytes, SHA256 `692017c353f894882ad0ff7d2336ff4ad13e1d91f8ba32fde109a6f5d580a0a7` |
| Preserved provenance adverse | 1,032 bytes, SHA256 `d8feb548e3be320ecef5a4bf4a91958f47d4e66cd5ad8ebebc20714c4d848802` |
| Input packet receiving | 13,814 bytes, SHA256 `4d5c9db4ad1d38942347af72ca5e2e83117ba958ee180266d8390671429c15c0` |

The author's 48 inert and 14 static checks remain author evidence; they were not relabeled as this review's work. The original native failures remain failures.

## Smallest prospective native discriminator

The minimal next observation is the exact reviewed route's default **two source-free ownership/confinement controls**, using its existing fresh owned output and exact source-commit CLI, without `--run-normal-pair`. This tests the repaired zero-status adoption and the actual bwrap-to-bootstrap capability transition while preserving every original receipt and strict predicate. It is not a request to enlarge a product matrix.

Both controls must produce natural bounded terminal/cleanup, complete bootstrap spec and operation receipts, all-five-zero actual ready/final status, NNP/seccomp, read-only probes, six raw transport denials, unchanged fixed/read-only input custody, and complete full inventories. A provider mismatch, missing SETPCAP, failed drop, changed identity, late exit, forced cleanup or incomplete observation must stop admission and retain a GAP. If root instead uses the existing optional normal-pair route, the source requires both source-free controls to pass before either original normal entry can start.

Actual installed-provider behavior remains unproven. This bounded PASS establishes no native result and does not authorize this reviewer to publish, dispatch, merge or close R0016.
