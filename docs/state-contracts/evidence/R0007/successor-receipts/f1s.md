# R0007 Firefox timing diagnostic — independent receiving

**Disposition: the single healthy source observation is received; latency cause, latency cure and pixel acceptance remain open.** Run **42890592160 / attempt 1**, job **130090383850**, actually released original `tomorrow:1` before its unchanged 10-second deadline and completed the expected Isha target render. This success does not repair the earlier Firefox acquisition, qualify its four dependent mutants, or establish whole native acceptance.

## Reviewer, independence and custody

Reviewer: **GPT-6 Astra Pro**, developer-provided identity self-report; backend identity was not independently attested. This is ordinary independent findings-only receiving, with no internal `audit-assess` route or lifecycle authority. I authored the prior exact independent timing review, SHA-256 `14c7531f1f9c007393d5c749ee5ff668fe3b88e94ba51a61f5a0e4f70e2c0704`; root authored the timing implementation. That unchanged source review is reused here. Root supplied controller context G0004 / d8849a3a; I neither inspected nor changed the controller.

The original ZIP is **696,859 bytes**, SHA-256 `4f37f98e65d2ba0cfaaf346f3ecb692e8481778bedc8d579d0a7b1eaeccd894a`. Its 25 members total **3,869,886 uncompressed bytes**. I verified the archive digest, member uniqueness and safe paths, CRCs, every extracted member byte-for-byte, and agreement with the saved member manifest. Retained GitHub metadata binds artifact **13798286660** to this run and head. Workflow success was corroboration, not the starting acceptance oracle. [E1–E2]

## Actual selection and source binding

| Binding | Received value |
|---|---|
| Published commit | `c5d46c3c02dd993fbf6746ec3591184e74cc2fb6` |
| Published/reviewed tree | `3d35264204e4660b8bf5c29dd3a257b7ab29f7ee` |
| Profile | `firefox-reordered-timing` |
| Actual selection | One headed Firefox `NE07-reordered24`, video-only |
| Timing driver SHA-256 | `96d64784068999f06c9768809b04f661a0fca279045f5b51fc939a91360983e2` |
| Request SHA-256 | `93cfa7e5cb9f9e6a13bbc01e426fd266dd7fbed00cda29182d99b38a18cd079d` |
| Selector SHA-256 | `cecfa9ed2a6155e2e96faf2a916d98902363c4755d1491f28083bda4d861ba4d` |
| Bound packet SHA-256 | `b457ac51c52f3232a9033ee4b94aed411731cff4180473a6d14fe2b45f614fd7` |

Packet, consumer manifest, selection and acquisition summary agree. Exactly one cell was planned and attempted, with none unattempted. All nine declared actions completed. The case-input file is **byte-for-byte identical** to the original FF20 reordered case. Its clock, response rules, body hold, action order, literal expectations and independent endpoint are unchanged. The old failed trace contains the identical first four action declarations, stopping at the failed release. [E3–E4]

I compared the two existing 147-entry source maps directly: **145 entries are unchanged**. The only differences are the reviewed timing driver and the separately added A06 recipe file. The selected reordered case is unchanged inside that recipe. Product, generated document, fixture, observer and scientific/runtime asset entries therefore retain their earlier identities; no 147-file disk rehash or 288-assertion campaign was repeated. The source HTML hash `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9`, instrumented HTML hash `edecab0bf2f1cfa88c6507b99bafc2292071393d3f61f71f9f2ac69a21831c4f` and fixture hash `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f` equal the earlier reordered acquisition. [E3–E4]

## Native identity and cleanup

The observed runtime is Windows Server 2022, image **20261101.353.1**, Python **3.12.10**, Node **v22.23.4**, Playwright **1.62.0**, headed Firefox **153.0**. Firefox executable SHA-256 is `9571c9a49d6d4de3e4c3b14e2e4bd6521e5b879f4ab6c95143e2098cb66e6618`. These environment fields and the complete browser identity equal FF20; this does not establish the same hosted machine, contention, cache state or latency. [E3–E4]

The owned consumer process exited normally with code 0. The final consumer summary exists and agrees with the trace, after the reviewed driver’s existing context/browser/Playwright/server cleanup path. The launcher reports `cleanupEstablished=true`; no timeout containment was needed. This is normal-exit and cleanup-path evidence, not a separate OS-wide orphan census. The exported prayer timer is cleared, pending boundaries are empty, and there are no unexpected requests or exported page errors. The remaining timer 12 is the ordinary 240-second poll timer recorded before browser teardown, not the settled prayer timer. [E3]

## FFT-01 — actual occurrence-one release and first completed target

All values in the following table use the **fixture-relative clock**. The deadline is independently consistent in both forms: timer start plus 10,000 ms, and owner `deadlineAt` 11,925 minus exported `startedPerformance` 590. Host monotonic spans are not mixed into this table. [E3]

| Event | Elapsed milliseconds |
|---|---:|
| Prefetch operation 4 / attempt 4, timer 7 starts | 1,335 |
| First completed current timetable, ordinal 2 | 1,382 |
| `tomorrow:1` body held | 1,389 |
| Original occurrence 1 released and JSON settled | 7,463 |
| Timer 7 cleared | 7,464 |
| First completed admitted target render, ordinal 6 | 7,519 |
| Unchanged original request deadline | 11,335 |

Release has a **3,872 ms deadline margin**. The first completed admitted target render follows release by **56 ms**. There is no timer fire, body abort, second tomorrow occurrence or substitute retry. Matching admitted tomorrow state and the completed render establish adoption by 7,519 ms. An exact adoption-callback timestamp is not exported; the settlement time is not relabelled as one. [E3]

The first such render selects **Isha, 00:31, 8 September 2026, UTC**, epoch **1788827460000**, with **91 minutes remaining** at fixed accepted epoch **1788822000000**. `.nt` is `00:31`; `.left` is `1h 31m left until Isha`; the selected timetable row and arc marker name Isha. The wall-interval progress is **0.7672634271099744**. The fixed clock remains `TIMESCALE=0`, `FOLLOW_WALL_CLOCK=false`, `ADVANCING=false`, and every retained runtime generation is 0. [E3]

I replayed only the reviewed driver’s pure `check_expected` function against this actual trace and the unchanged literal case expectations. All **three stage groups** pass: unavailable, first-current and matching-tomorrow-settled. No browser driver main or source test suite was executed. The automatic status remains **SOURCE_ASSERTIONS_MET_PIXELS_PENDING**; this replay establishes the same bounded source-observation scope. [E3, E5]

## FFT-02 — actual host spans locate costs, without establishing a cure

All 21 timing rows have ordered `host-monotonic-ns` start/finish values, matching elapsed values and ordinary return completion. Relevant spans are: [E3]

| Existing operation | Action index | Host elapsed ms |
|---|---:|---:|
| Navigation to DOMContentLoaded | — | 4,953 |
| First current-timetable wait | 0 | 422 |
| Held occurrence wait | 1 | 46 |
| Unavailable first-receipt read/evaluate | 2 | 594 |
| Unavailable before-ordinal read | 2 | 344 |
| Unavailable bounds read | 2 | 1,687 |
| Unavailable after-ordinal read | 2 | 16 |
| Unavailable presentation file write | 2 | 0 recorded |
| Original occurrence release | 3 | 0 recorded |
| JSON-settlement wait | 4 | 16 |
| Later read-only checkpoint receipt | 6 | 4,765 |
| First-current historical receipt read | 7 | 1,453 |

The pre-release unavailable capture consumes **2,641 ms** in its recorded existing calls. Navigation through release-call start spans **8,062 ms on the host clock**. Equal start/finish readings on short operations do not mean zero physical cost. Each page call combines host dispatch, browser work, protocol transfer and decoding; the bounds span does not by itself prove layout was the sole cost, and the receipt span does not isolate serialization. [E3, E5]

There is also a **6,172 ms gap** between the settlement wait’s finish and the checkpoint receipt call’s start. The only declared intervening action is the existing **250 ms Python `time.sleep`**. Untimed loop/bookkeeping and host scheduling are also inside that gap. The packet does not identify the sleep’s exact entry/return or a causal owner for the extra interval. This is **after successful release**, so it cannot explain a pre-release expiry in this run. It shows why this success cannot be described as a generally low-latency acquisition. No extra native run is needed merely to restate that limitation. [E3, E5]

In original FF20, timer 7 started at 1,298 ms, its body was held at 1,347 ms, and the actual abort occurred at the unchanged 11,298 ms deadline. No occurrence-one release or settlement exists. The subsequent `No pending boundary tomorrow:1` failure has no call timestamp; its relation to the exported retry cannot be invented. That trace has no host-operation spans, so this later successful span distribution cannot retrospectively locate its missing delay. Both runs are video-only and use the same case bytes and browser executable. A deterministic first-case failure is not supported by this successful first case; a cold-start or host-scheduling cause remains unproved. [E4]

## FFT-03 — font metadata and source/pixel distinction

The native export reports **24 faces with `display: swap`**, comprising **3 loaded and 21 unloaded faces**. The loaded faces are Fraunces weight 400–700, Inter 400 and Inter 600. Final FontFaceSet status is `loaded`; the authored startup observer reports zero pending deferred receipts and no lifecycle errors. It retains trusted Document LINK load observations with print and all media and genuine FontFaceSet loadingdone/deferred receipts. This reordered case has **no async font-barrier action**; the final records do not imply that such a barrier guarded its release. [E3]

These are actual read-only descriptor/status observations at export. They do not identify which face painted any glyph, establish a video clock map, recover previous provider responses, or resolve the earlier partial-text intervals. No font cause or font-policy countermeasure is established here.

The original video is **389,935 bytes**, SHA-256 `916adbb81f5a9c149d83225f5c65367dd008a36e164ee251d7596bb4903f5a2e`. There are no still screenshots. The unavailable capture selects historical receipt ordinal **2** while its before/after ordinals are **5/5**; that mismatch remains explicit. First-current records **6/6/6**, which supports a source association but does not itself identify the first visible video frame. Actual-arc is eventual-state evidence. I did not inspect pixels in this receiving lane. Independent first-visible review and the prior readability findings remain open. [E3]

## FFT-04 — smallest bounded next acquisition

The four old negatives remain **unqualified**. This one-cell diagnostic contains no mutant, and a later healthy run cannot be substituted for the failed same-acquisition companion.

The smallest fresh complete dependent set is **six headed, video-only Firefox cells**:

1. `NE07-reordered24`
2. `NE07-ordinary24`
3. `NE07-mut-hardcoded-fajr`
4. `NE07-mut-name-order`
5. `NE07-mut-lost-date`
6. `NE07-mut-independent-label`

Each negative explicitly requires **both** reordered24 and ordinary24 as healthy companions; a five-cell set would omit a required fresh positive. The next purpose would be new discrimination evidence for these four controls, with the current host spans available if pre-release latency recurs. A finite selector/request change requires its own bounded exact review before root publication or launch. This report does not certify that future source or grant launch authority. [E4–E5]

Preserve the existing case bytes, literal assertions, occurrence-one release, 10,000 ms product deadline, capture order, native fonts and timing observations. Receive every new outcome on its own evidence. If another original-occurrence expiry occurs, retain it and use that failure’s recorded spans to choose a concrete next discriminator; do not repeat unchanged acquisitions until green. The current wrappers already cover the previously missing pre-release calls. This artifact supports **no product deadline, target-oracle or font behavior change** and no broad repeat of the accepted source campaign.

The separate Chromium/A06 scopes, whole-contract review, R0017 integration order, exact owner approval, actual merge and public delivery/readback remain root-owned obligations. No whole native PASS, merge approval or issue closure follows from this receiving.

## Evidence and effects

- **E1:** [Original diagnostic ZIP](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/r0007-windows-native-42890592160-1.zip) and [archive receipt](sandbox:/workspace/scratch/66b3aaff4329/recovery/native-42890592160-1/archive-receipt.json).
- **E2:** [Retained GitHub metadata](sandbox:/workspace/scratch/66b3aaff4329/recovery/native-42890592160-1/github-metadata.json) and [extracted-member manifest](sandbox:/workspace/scratch/66b3aaff4329/recovery/native-42890592160-1/extracted-manifest.json).
- **E3:** [Actual trace](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42890592160-1-original/r0007-native-aljt7vol/firefox/NE07-reordered24/attempt-0001/consumer/NE07-reordered24/trace.json), [source manifest](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42890592160-1-original/r0007-native-aljt7vol/firefox/NE07-reordered24/attempt-0001/consumer/input-manifest.json), [case input](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42890592160-1-original/r0007-native-aljt7vol/firefox/NE07-reordered24/attempt-0001/consumer/NE07-reordered24/case-input.json), [adjudication](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42890592160-1-original/r0007-native-aljt7vol/firefox/NE07-reordered24/attempt-0001/adjudication.json) and [request selection](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42890592160-1-original/request-selection.json). The JSON companion contains compact source/timing/custody derivations and complete 21 operation rows.
- **E4:** [Original Firefox20 ZIP](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/r0007-windows-native-42834337271-1.zip) and [exact recovered receiving report](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox_affected_receiving.md).
- **E5:** [Prior exact timing review](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/latency_diagnostic_exact.md), [bound frozen timing driver](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/latency-diagnostic/candidate-3d35264204e4660b8bf5c29dd3a257b7ab29f7ee/tools/cp9/r0007_browser.py) and [this receiving JSON](sandbox:/workspace/scratch/66b3aaff4329/recovery/reviews/firefox_timing_receiving.json).

Only the assigned receiving Markdown and JSON were written. Original evidence, earlier reports and candidate source stayed read-only. No browser, server, install, network, native launch, workflow, source/index/ref or controller mutation occurred.
