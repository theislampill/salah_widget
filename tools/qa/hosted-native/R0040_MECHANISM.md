# R0040 main bracket and protocol metadata diagnostic

This is a separate opt-in source diagnostic based on the frozen all-stream
`f3ba20bf8c97baf61388401ab7397739003ff51d` tree. It selects no campaign and records
no native result. The implementation plan is [R0040_MECHANISM_PLAN.md](R0040_MECHANISM_PLAN.md).
The original [Date-only](R0040_DATE_ONLY.md), [passive](R0040_PASSIVE.md), and
[central passive](R0040_PASSIVE_CENTRAL.md) requirements remain mandatory.

## Selection and preserved source

The new selector is `r0040Mode: "capture-mechanism"` or
`--r0040-mode capture-mechanism`. Its only population is `workOrders: ["R0040"]`,
Chromium DPR1, with the original bday/moderate/M1/common cell. The lane ID is
`r0040-chromium-capture-mechanism`; its result kind is `r0040-capture-mechanism`.
It cannot share a supplemental route budget. Existing mode names retain their
existing entry files, identities, original arguments and result meanings.

The new leaf is `r0040_mechanism.cjs`, a subclass of the byte-identical reviewed
passive retention class. The eight arguments after `--` still mean acquired
Playwright package, prepared historical root, prepared main root, fresh capture
output, `chromium`, `bday`, `moderate`, and `M1`, in that order. The original
preparer, capture driver, Date-only helper transformation, passive sampler,
worker observer, product/worker code, frame listener, ACK, stop expression and
lossless verifier have no source edits.

The operational diagnostic is explicitly extended: it transforms two exact
callables before their original browser evaluation. It does not claim an
operationally unmodified driver. Digest checks and exact inverse recovery bind
the only permitted seams:

| Input | SHA-256 or exact recovery requirement |
| --- | --- |
| Original complete `tools/qa/r0040/capture.cjs` | `19a766ccacf0ac784f46961a5cd0079390f10a34d14825ef5ac7b28adbd33e26` |
| Original main installation callable | `ec300b48e036c198b5ad0a8b7c2eb3081453552e19420dac5c319a5ab4ab95ec` |
| Original isolated sampler | Existing unchanged passive transform first verifies its original source; reversing the new extension recovers that exact passive expression, and reversing passive recovers the original. |
| Original passive leaf | `7386366a391cb7e401d11a36da691771b1d88a09fa8c16584093184ebd8a7a5e` |
| New bracket helper | `b2a2e73433055ab90f4ae617f70268e0d5f02563e36c6a5ffc071ce0445c5757` |
| New network helper | `77d40fa3519d0328fb3fcfda34f5c5001e0d82790b365801f989a5126a978af7` |
| New leaf | `cc7a791fba7438a36743a424d6bd063289217b54bea05ec10be07206356abf93` |

The runtime identity additionally includes each transformed callable digest,
installer digest, exact inverse result, snapshot expression, full old passive
identity and collector limits. The central helper checks the fixed new and old
leaf pins. Current preparation also binds exact path/byte-count/hash records
for `r0040_mechanism_central.py`, `r0040_passive_central.py`, `lanes.py`,
`observe.py`, `capture_pipeline.py`, `prepare.py`, and `r0040_capture_prepare.py`.
These caller hashes are measured from the actual source path and compared on
fresh readmission; they are not rewritten old preparation receipts. The
regression registry declares the complete imported/transformed input closure.

## Main-world brackets and the same event join

The original main `r0040-read` listener body is passed unchanged to a wrapper.
For each call, that wrapper records its ordinal and the native event stamp,
reads main-world `performance.now()` immediately before the original call,
invokes the original once with its original receiver and arguments using
`Reflect.apply`, and reads the same performance clock in `finally`. It returns
the original result or rethrows the identical original exception. Clock or
observer faults become separate incomplete evidence. It never wraps the
`__r0040Sample` function itself, so the original earlier direct geometry read
does not become a new sample ordinal.

The isolated extension adds one read-only listener to the same bus. During the
same synchronous dispatch it records `samples.length` and the native event
stamp before the original sample push. It does not write bus text, dispatch an
event, call the original sample function, request a frame or install a timer.
The original main sample fields and isolated passive rows remain separate.

After the unchanged passive adapter has retained the actual original stop
response and its own sampler extraction, the new leaf extracts the main and
join snapshots in parallel. It returns the exact original stop object. A
failure-path snapshot before context close is tagged as an incomplete prefix;
it cannot stand in for a completed post-stop extraction.

The bracket inspector requires the actual stop Buffer, complete old sampler
population, exact consecutive ordinals, one unique matching native event stamp
per ordinal, finite successful main brackets, zero loss/faults, unchanged
clock/Date identities, and the original source-admitted startup Date anchor.
It preserves the exact Date-only formula and operation order:

```js
Math.floor(utcMs + mainPerformanceMs - anchorPerformanceMs) - utcMs
```

Every actual original `phaseMs` must lie between that formula evaluated at its
main before/after bracket. Original `at == isolated.timeOrigin + rAF timestamp`
remains an independent old passive requirement. Main and isolated time origins
are never assumed equal. Event stamps are identity joins, not substituted
performance readings.

For interpretation only, each synchronous dispatch bounds a possible constant
offset mapping the main clock into the isolated clock. Its lower bound is
`isolatedEntry - mainBefore`; its upper bound is
`isolatedAfter - mainAfter`. Intersecting those bounds yields either
`BOUNDED_CONDITIONAL_OFFSET` or `UNRESOLVED_CLOCK_BRIDGE`. The explicit assumption
is a stable unit-rate offset. An empty intersection is retained as unresolved;
it does not invalidate an otherwise complete bracket population or authorize
cross-clock subtraction. Neither outcome repairs timestamps, establishes a
cause, changes the original verifier, or qualifies cadence.

The separate pure arithmetic control uses only numbers already declared to be
in one clock. It checks that Date-versus-rAF residual equals callback-lag change
plus the change in integer rounding residual. Constant lag cancels. Prior
startup observations are not evidence that later capture ordinals share that
same causal relationship; only actual retained per-ordinal brackets can narrow
that uncertainty.

## Read-only protocol metadata and its coverage limits

The collector uses the public browser CDP session and its public event/send
methods. It requests page/worker target discovery, records target changes and
destruction, and manually attaches without pausing targets. Nested public
Target messages enable Network metadata on those sessions. It never requests
auto-attach, a debugger pause/resume, a Runtime/Page command, cache/routing
changes, response bodies, or worker-consumer instrumentation.

Only the exact loopback capture-origin paths `/moon/assets/dem.bin.gz` and
`/moon/assets/colour.bin.gz` are selected. The retained fields include target
ID/type/URL/context, owned protocol session, protocol request ID, method/URL,
bounded initiator frames, response status and selected metadata headers,
received byte counts, and loading-finished or loading-failed terminal fields.
Protocol timestamps and Node monotonic receipt times remain different clocks.
No subtraction between those domains is reported.

The public target attach can race early worker requests. Unsupported APIs,
missing starts/responses/terminals/ownership, redirects, duplicate identifiers,
unfinished targets, or ambiguous matches therefore make this component
`INCOMPLETE`. Startup policy is not altered to force coverage. A complete join
requires exactly one selected original GET per asset, one protocol occurrence
per URL/method, a known session/target lifecycle, and a unique original
`worker-constructed` URL match. Both protocol and original request IDs remain
in the result; they are not asserted to be one identifier namespace.

`loadingFailed` is an observed terminal when its ownership and population are
complete. It remains a failure. `loadingFinished` records protocol loading
completion only. Even a canceled flag cannot identify the JavaScript caller
that canceled. `javascriptReaderCompletion` and `readerCancellation` remain
`NOT_OBSERVED`; cause remains `NOT_ESTABLISHED`. This diagnostic cannot establish
that a stream reader reached `done`, that source-level `finally` cancellation
caused an abort, or that Moon refinement reached its final state.

Nested protocol errors may arrive before the public send acknowledgement. The
collector attaches a rejection handler immediately and subsequently retains the
same error as diagnostic incompleteness. It does not leave an unhandled promise
rejection capable of replacing the original operation's result.

Final collection has a separate completion fence. After existing attachments
settle, the collector records its target/session lifecycle version and awaits
the existing final public target snapshot. Before removing its own listeners,
it synchronously records the resulting version and pending attachment/response
counts. Both counts must be zero and the lifecycle version must be unchanged.
Creation, target-info changes, destruction or session detachment during that
request therefore retain `INCOMPLETE`, even if the late work already completed.
Offline inspection also checks this boundary against the retained lifecycle
rows. Attachments started during final collection share the existing drain
deadline; there is no extra command, wait, poll, paused target or coverage
waiver. A returned incomplete snapshot stays incomplete if a late attachment
subsequently times out.

This fence corrects independent synthetic finding R0040-M1 on the preserved
`3f67dc517b067261153395121427c570d92a97a7` author tree. That tree could mark its
drain observed while a target created and destroyed during the final public
snapshot still had an outstanding attachment. Its original successful source
gate and the independent RED controls remain historical evidence. The finding
does not establish a native occurrence, an original-verifier bypass, an asset
abort cause or a relationship between startup and later capture ordinals.

## Independent completeness and retained evidence

`mechanism-observation.json` is a separate receipt. Its `bracket` and `network`
inspection statuses are independent: either complete component remains
readable when the other is incomplete. The combined diagnostic is complete
only when both are complete. The existing original and passive receipts and
the original raw stop artifact remain unchanged.

The journal adds a source identity, one bracket prefix, network prefixes before
context creation, at original readiness return, and after original context
close, plus an observation-ended record. The final network prefix follows the
bracket extraction. The original `driver-process-ended` and
`passive-terminal-status` remain second-last and last respectively. New fields
are never appended into original samples, raw stop bytes or original receipts.

The ordinary Date-only gate still checks the original report, clock proof,
request/cleanup outcomes, current namespace and full original source/preparation
population. A single new central replay then reopens actual regular artifacts,
checks their bytes/digests, and calls the unchanged passive admission with the
actual original Buffer as its mandatory sixth argument. The new admission
adds the two independent diagnostic checks without bypassing that call.

An observed success label is only
`ADMITTED_MECHANISM_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION`, with timing
`instrumented-mechanism-passive-date-only`, `nativeQualification: NOT_VERIFIED`
and `humanAcceptance: OUTSTANDING`. Actual child exit 1, timeout, continuation
veto, namespace failure, any original failure, incomplete new data or changed
source cannot become that label. The producer gate separately verifies the
exact combined replay command, current raw artifact references, original
Date-only/passive status, nested namespace result and both component states.
Failure records remain eligible for complete failure retention under the
unchanged strict transport; a diagnostic label cannot turn failure into
qualification.

## Bounds and controls

All ceilings are uncalibrated. The child stays at 240 seconds: original driver
180, old passive evaluations 20, new setup 5, parallel new extractions 5, new
network drain 5, and remaining serialization/finalization reserve 25. Setup and
drain deadlines use the host monotonic clock. No new command starts after an
expired deadline or an unfinished drain. No new scene wait, frame or delay is
added. Source readmission remains 120 seconds; Date-only checks plus the single
combined 30-second replay remain 130; boundary allowance is 75. The lane is
565 seconds, preparation 1,350 plus outer readmission 120, and the selected
coordinator/workflow limits stay 2,640 seconds/45 minutes.

| Population | Ceiling |
| --- | ---: |
| Original samples/main brackets/event joins | 4,096 each |
| Actual original stop bytes | 8 MiB |
| Worker/page targets | 16 / 4 |
| Selected requests / all tracked protocol request IDs | 16 / 256 |
| Network metadata rows / serialized metadata | 4,096 / 2 MiB |
| Initiator frames / text field / protocol message | 8 / 1,024 characters / 256 KiB |
| Retained protocol issues | 32, with full fault counter |
| New mechanism final receipt | 4 MiB |

Overflow and truncation retain bounded prefixes and original counters. They
cannot imply complete coverage. Focused synthetic controls cover exact
transforms/inverses, actual payload/receiver/return/throw behavior, original
sample/stop/callback parity, joins and clock arithmetic, protocol ownership,
missing/duplicate/overflow data, early nested rejection, exhausted drain,
current source/runtime/canonical command, actual exit/namespace precedence,
and coupled producer-record substitutions. Namespace/current generated-source
success uses explicitly identified test doubles; actual leaf replay reads
real synthetic artifact files. No source test establishes native coverage,
performance, product acceptance, final Moon refinement or an abort cause.

The original author freeze `3f67dc517b067261153395121427c570d92a97a7` and its
evidence remain preserved. This successor composes that exact diagnostic onto
the reviewed T1 base `d460d0b6060b4d0912541a08a158a7526d4802a1`. The complete
ordered one-lane population and canonical recipe are checked before any new
currentness child. Mechanism readmission requests actual raw streams, and T1
`retain_currentness` binds the exact mechanism entry path, acquired Python,
working directory, unchanged 120-second bound and known returned result.
Only a known completed refusal or waited timeout yields a retained `NOT_RUN`
record; malformed, exceptional, foreign, interrupted or incomplete process
records remain unsealable. A zero process exit with malformed output is not
refusal authority. The original plan is never rewritten. The old passive raw
readmission and all fourteen original T1 controls remain unchanged.

No old preparation can authorize changed caller bytes. Independent full-tree
review and genuine current preparation remain prerequisites for any later
native selection. No campaign, strict transport/envelope behavior, native
predicate or source budget is relaxed by this composition.
