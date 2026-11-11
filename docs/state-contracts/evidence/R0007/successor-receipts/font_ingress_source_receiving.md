# R0007 controlled font-ingress source receiving — FINAL findings

**The two-arm comparison was not realized.** `NE07-font-fallback-fall24` failed in the original case-action phase, at zero-based action 3 (`release capture-current`), before the font-ingress experiment could run. The original current-body timer fired and aborted its held body. The native trace locates that failure and its missing prerequisite, but does not identify why the host spent 7.640 seconds between the preceding capture write and release invocation. The baseline completed its source assertions and font transaction custody; its first-current presentation association remains partial. No source-only contradiction establishes a product repair or a Gecko fault.

This is an independent, authoring-independent **findings-only** receiving report for one actual acquisition. It confers no currentness, formal audit disposition, native acceptance, whole-R0007 acceptance, publication, execution or lifecycle authority. Root retains those decisions. The primary native failure is preserved.

## 1. Exact scope and custody

- Published source object: commit `4bac6a4781fce62f08ab550a20fe5234d3ebb746`, tree `a5e51a591200296e3e73b9ecedbd8c0539e07ee5`, parent `c373cbdc706cf3b27ab8c45dbde02a998bd1fbd4`. Only these immutable objects were inspected; this reviewer did not inspect or change current refs, index, controller or publication state.
- Acquisition identifiers supplied by root: run **42920631317**, attempt **1**, job **130194259457**, artifact **13811167788**. The archive's summary independently records run and attempt. The job/artifact identifiers are receiving-envelope metadata, not independently queried from a service here.
- Original archive: `/workspace/scratch/66b3aaff4329/native-artifacts/r0007-windows-native-42920631317-1.zip`; **3,111,326 bytes**, SHA-256 `50e90fb8196e73d9a9af5ac5bc68ba9f95df032c524980e73a4fdb0aa028e5e5`.
- Exact original extraction: `/workspace/scratch/66b3aaff4329/native-artifacts/42920631317-1-original`; body `r0007-native-vxzmg9lz`. **All 40 members compare byte for byte with the archive, with zero extra extracted files.** No originals were modified.
- Baseline trace: 4,537,415 bytes, SHA-256 `e3d3bd4dcea4cd5b950a6d99388b1dd835b93db7a91fae59e69b817c1cbca655`.
- Fallback trace: 639,728 bytes, SHA-256 `f9fb980c99bde9f6bf4e85914484ff32d72733b0c7af14dc74c07d0a67ef04cd`.
- Bound packet: SHA-256 `501db54d24d050a734677c87511e38e04ff79185a7270cfcfe528140c5e916e5`. Both consumer input manifests have SHA-256 `75083af42298719fcfda087cc3a2ee880ff43274613e517985016b69c662e7c9` and bind the same packet and all 150 source files.

Every original file's path, length, digest and extraction comparison is retained in [input-custody.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/input-custody.json). The observations and checks below are reproducibly projected in [read-analysis.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/read-analysis.json). These derived records supplement the originals; they do not replace them.

## 2. Setup, command and source bindings

All five setup commands returned exit 0 with no recorded setup error: Python version, Node version, venv creation, pinned Playwright package installation, and the browser installation command. Actual recorded versions are Python **3.12.10**, Node **v22.23.4**, Playwright **1.62.0**; host Windows **2022Server**, AMD64, image **20261101.353.1**. Installation logs show Firefox **153.0**, Playwright build **1538**. Chromium was installed by the unchanged setup but was not selected or executed in this acquisition.

Both cases report Firefox 153.0, `headless=false`, managed executable `D:\a\_temp\r0007-browsers\firefox-1538\firefox\firefox.exe`, SHA-256 `9571c9a49d6d4de3e4c3b14e2e4bd6521e5b879f4ab6c95143e2098cb66e6618`. The exact driver hashes that resolved executable before launch and passes the same path explicitly to `launch`. The Windows binary itself is not in the received archive, so this is a bound native launch receipt, not a second local hash of the executable. Context creation requests viewport 370×570, DPR 1, America/New_York and default `no-preference` motion; presentation receipts record viewport 370×570 and the observed card bounds are 325×530. No independently sampled system-font inventory or per-glyph font selection is retained.

The committed request selects only `firefox-font-ingress`, two serial headed, video-only cases, with arguments:

```text
--engine firefox --headed --video-only
--recipe tests/rlgwo/R0007-font-ingress-recipes.json
--case-id NE07-fall24 --case-id NE07-font-fallback-fall24
```

The actual workflow invokes `tools/qualification/r0007_native_request.py --source-root $env:GITHUB_WORKSPACE --evidence-root $env:R0007_EVIDENCE` using its private venv Python. Each retained producer command then runs that same private Python against `D:\a\salah_widget\salah_widget\tools\cp9\r0007_browser.py`, issue 7, Firefox, the bound case packet, the run's capacity lease, its own consumer output directory, one exact case ID, `--headed --video-only`. Complete argument arrays, executable paths, PIDs and UTC start/finish times are retained in `read-analysis.json` from the original producer receipts. Baseline producer exit was 0; fallback exit was 1. Both terminal states are `exited`; neither hit the 240-second supervision timeout. There were no unattempted selected cells. The launcher exited 1 and selection status is `ACQUISITION_NOT_ACCEPTED`. Workflow failure/upload success are root's platform receiving facts; no workflow service was contacted by this reviewer.

**All 150 recorded bound source hashes equal the exact commit's blobs.** The bound cases equal the committed ingress recipe; each equals its original FUSE case after removing only `fontIngress=late-css-held-fonts-v1`. Across the two arms, the case values differ only in `caseId` and the existing `variant=font-fallback`. All seven actions, inputs, cache seeds, literal expectations, clocks and deadlines are preserved. The fixture variant removes the two leading optional font families from their existing lists; native fallback snapshots confirm Georgia/Times/serif for the display surfaces and system-ui fallbacks for body/date surfaces.

The r2 candidate manifest's eight files match the exact published commit and its candidate tree; the commit's changed paths match its eight-path list. The prior source review was read only for this provenance join. Its source/control result is not used as native acceptance.

| Exact published path | SHA-256 |
|---|---|
| `src/native/index.html` | `e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037` |
| `index.html` | `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9` |
| `offline.html` | `697ed290d2f71a777b9c1a44c3d7b12350cd51dfc66648e8c8907ff897e9be57` |
| `tests/rlgwo/prayer-browser-fixture.cjs` | `50642398dbb3ebacb36912cb2977b69e1520d60aaaf5f2dc4d2de63db6c107d2` |
| `tools/cp9/browser_runtime.py` | `af7e6376ac8fe3c731ea1e215dac37faadc48f1f766a6bdf32637426e1daa4e0` |
| `tools/cp9/r0007_browser.py` | `080e9a9529b21134ae923a713cef14168297c53b7ddee8ffeb18f3d6e673f397` |
| `tools/cp9/r0007_font_ingress.py` | `988f58d68c72f9ae62537f77b4ef7a47bf87eee29cfb6a31fb173c59944647ab` |
| `tools/cp9/r0007_font_observer.js` | `9b5adb0d9398a8c98dd41fbdd333dd6b7e2b250e1cd4459cbd99929f24f867c0` |
| `tools/qualification/r0007_native.py` | `5df9d426b3b03cb49a7516db37213896f151af9261f4d62df4399809811d4856` |
| `tools/qualification/r0007_native_request.py` | `56e52f6525d18111658fe79e880f7f25fe5830d3f328eeb5e53b72df09b3bac1` |
| `tests/rlgwo/R0007-font-ingress-recipes.json` | `e67108cd22a73489dd3a8fc9e96796fb0b40795836edf247dc15c474a92f1fe4` |
| `tests/rlgwo/R0007-native-request.json` | `de8c00da173b60a79d888e6a682d595ff87d9afef071aabc12ddeda9bcb923d3` |
| `.github/workflows/r0007-native.yml` | `d6f3fb404a8622bb283bade798efb74d62cb77d23b005d57eff2ddab75aa10c2` |

The generated document receipts bind `index.html` and the fixture hashes above. Recorded observed HTML digests are `71e821728a5e99403be27dd709eb986768b054653c34d8f762561d8c7ef4ff22` for baseline and `9c699ab5fb4fe820856587bc87172514800b8414e0d1dd1b946ca432dd7f0846` for fallback. The generated served HTML bytes are not separately retained in the archive. This review did not regenerate them or replay the fixture.

## 3. Original seven actions and the exact failed boundary

Times below are **recorded host monotonic seconds**, not video timestamps. Capture ranges span their recorded suboperations. The sleep has no operation timer of its own.

| Index | Original action | Baseline host span/result | Fallback host span/result |
|---|---|---|---|
| 0 | Wait for pending `capture-current:1` | 249.125–249.234; returned | 282.187–282.281; returned |
| 1 | Read-only loading capture | 249.234–250.765; returned | 282.281–283.828; returned |
| 2 | `sleep 250 ms` | Action recorded; no isolated span | Action recorded; no isolated span |
| 3 | Release `capture-current` | 256.093–258.156; returned | **291.468–291.546; Error, returned=false** |
| 4 | Wait for actual current-day completed render, 15,000 ms bound | 258.156–258.656; returned | Not reached |
| 5 | Capture earliest matching `first-current` receipt | 258.656–259.515; returned | Not reached |
| 6 | Capture latest `actual-arc` receipt | 259.515–260.046; returned | Not reached |

Navigation returned at 249.125 baseline and 282.187 fallback. Baseline has all seven action records. Fallback has the first four, because the driver records an action immediately before attempting it; the fourth record is not evidence of successful release.

The critical uninstrumented regions are:

- Baseline: `capture.presentation-write` finished **250.765**, release measurement started **256.093**: **5.328 seconds**.
- Fallback: `capture.presentation-write` finished **283.828**, release measurement started **291.468**: **7.640 seconds**.

The exact driver path in between contains the end of the loading-capture branch, loop dispatch/action bookkeeping, and the unchanged `time.sleep(action['ms']/1000)` for action 2. The loading action has neither preservation nor first-render work. There is no post-action fixture read, `ingress.check`, browser/protocol call, new readiness wait or font-ingress operation in that source interval. The program enters the next measured operation before calling `frame.evaluate` for release.

**Existing receipts cannot subdivide these gaps further.** They do not time the sleep call, report Python runnable/descheduled intervals, or locate host dispatch suspension. They establish a 250 ms requested sleep and a much longer surrounding elapsed interval; they do not prove the actual sleep duration or a particular scheduler, renderer, recorder, provider or Gecko cause. The 78 ms failed release call is distinct from the preceding 7.640-second gap. The later 15-second current-render wait never began in fallback.

### Actual page timer/body evidence

All elapsed values in this subsection use the fixture's own page elapsed clock; they are not aligned to video or to an exact host origin.

| Evidence | Baseline | Fallback |
|---|---|---|
| Current prayer timer | ID 6, 10,000 ms, start +845 ms | ID 5, 10,000 ms, start +840 ms |
| Original held body | `body-hold` +845 ms | `body-hold` +841 ms |
| Successful release | +10,660 ms | No release event |
| JSON settlement | +10,661 ms | No settlement event |
| Timer outcome | Cleared +10,662 ms; no fire | **Fired +10,856 ms; `body-abort`, ignoreAbort=false** |
| Following state | Current adopted; prefetch obtained | Timer cleared; original 900 ms retry sleep began; no adopted current receipt |

Baseline cleared its timer 183 ms before its nominal page-elapsed due point (+10,845 ms). Fallback's timer fired 16 ms after its nominal due point (+10,840 ms). Its body abort is a positive original observation, not an inference from exit 1.

The exact product source starts a 10-second attempt timer covering fetch and JSON body. Its cancel path aborts the controller and rejects the attempt; the fixture's non-ignored abort settles and deletes the pending key. The fixture's release function throws when that key is absent. The recorded timer fire/body abort/no-release sequence therefore supports **loss of the held-body prerequisite** and explains the source path that can reject release. The preserved external exception is only `Error: OMITTED_UNTRUSTED_ERROR_TEXT`; it does not retain the actual exception string or prove a specific underlying protocol error. Do not present the source's possible “No pending boundary” message as an observed native message.

Fallback `failureStage=case-actions` plus the release operation identifies the actual failed phase. Its `fontIngress.hostEvaluations` and `observations` are empty; `css={}`, `fontRequestCount=0`, `retainedFontBytes=0`. The helper experiment after the seven actions did not start.

## 4. Literal source oracles and presentation limitations

Baseline's earliest actual populated completed-render receipt is ordinal **2**, fixture elapsed **10,723 ms**. Original populated render ordinals **2–7** agree on the following; checkpoint copies are not additional independent renders:

| Field or surface | Original observed value |
|---|---|
| Current event / `.cn` | Isha |
| Next event / next marker | Fajr; `.arc` has `circle.dot.next[data-prayer-key=Fajr]` |
| `.nt` / next time | `05:00` |
| Countdown | 270 minutes; `4h 30m left until Fajr` |
| Accepted UTC epoch | 1,793,511,000,000 (`2026-11-01T05:30:00Z`) |
| Target epoch | 1,793,527,200,000 (`2026-11-01T10:00:00Z`) |
| Timetable date / next date | `01-11-2026` / `01-11-2026` |
| Zone | America/New_York |
| Selection / progress kind | `same-day-target` / `decorative-before-first` |
| Progress / minute coordinates | 0.631578947368421 / previous −270, next 300 |
| Card | 325×530 |
| Gregorian / Hijri date | `2026-11-01` / `1448-02-19`; selected current-day source, before Maghrib, no roll applied |

The literal UTC endpoint difference is 270 minutes. The prayer row markup marks Fajr `on` and Isha `now`; Sunrise is a ring in the arc. All six rows have the recipe times. The existing expected equality, contains, numeric-range, marker regex and invalid-text checks match independently against retained JSON. These are source/DOM findings, not pixel readability findings.

Baseline `first-current` selected receipt ordinal 2 while capture before/after ordinals were **3/3**. The original collector correctly retains `UNVERIFIED_ORDINAL_MISMATCH`, status `PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED`, and `SOURCE_ASSERTIONS_MET_PIXELS_PENDING`. Source selection of an early completed receipt does not prove which video frame first presented it.

Fallback has no populated render, no successful current adoption and no realized source oracle. Its initial loading receipt remains at null current/tomorrow dates, `render=null`, prayer/date unavailable text. It is a healthy comparison case with `expectedFailure=false`; its exit 1 is not an intended mutant rejection.

## 5. Baseline controlled ingress, native transactions and phase timing

Both arms installed the same routing before navigation. Routing disables all HTTP caching in both contexts, including potential timing changes to unrelated assets. Empty fixture cache seeds do not restore an ordinary-network control. Historical unrouted FUSE is not a matched control for this routed occurrence.

Baseline completed all seven original actions before media observer installation and ingress. Its phase receipts are:

| Phase | Host evaluation bracket (s) | Page read span (ms) | Ordinal | Registered relevant faces |
|---|---|---|---|---|
| Before CSS | 260.078–260.156 | 12,960–12,960 | 3 | 0; link print, no terminal |
| CSS applied | 260.812–260.890 | 13,683–13,685 | 3 | 3 loading, 21 unloaded |
| Fonts-held end | 262.937–263.093 | 15,886–15,887 | 3 | Same 3 loading, 21 unloaded |
| After fonts | 268.312–268.421 | 21,136–21,137 | 7 | 3 loaded with deferred done receipts, 21 unloaded |
| Post-tail cut | 269.687–275.109 | 27,902–27,903 | 7 | Same settled state |

The source retains a 500 ms pre-CSS observation wait, 2,000 ms font-hold observation wait and 1,000 ms native presentation tail. These requested windows are not exact native video durations. The final host evaluation itself spans **5.422 seconds**, although its retained page read spans 1 ms; this is another reason not to convert host call boundaries into frame alignment. Finalization is recorded at 275.109, before the recorded settlement deadline 278.093.

### CSS custody

The exact original-link URL is the declared Google Fonts CSS request for Fraunces opsz/weight and Inter 400/500/600 with `display=swap`. Request **1** was observed at host 247.531, held, then fulfilled at 260.781. Its native response **1**, status **200**, MIME **text/css**, and `finished` terminal were recorded at 260.812. The source uses `route.fetch` then successful `route.fulfill(response=api_response)` without response body/header/status overrides. The API response was disposed.

The retained CSS is **8,938 bytes**, SHA-256 **`6568c2adf86e353a7d1d8641deb8b5cecdd49d571377c6c90e9f48dd3bef8e18`**. Its independently read file hash equals the API-body, delivered-CSS and separately captured native-response body hash receipts. Native body availability is `captured`, not unavailable. The body contains **24 face declarations and 10 distinct declared URLs**. The current connected original link, trusted load and `media=all` application are bound in the applied observations.

### Native font requests and retained bytes

| Request → response | Resource candidate | Continue invocation (host s) | Native response/finish (host s) | Retained bytes / SHA-256 |
|---|---|---:|---:|---|
| 2 → 2 | Inter Latin URL | 263.093 | 263.312 | 48,532 / `acc60d454f46f2ba233c516aa3299aa60e1f49ffd0f06b8392a7c772a5694087` |
| 3 → 4 | Fraunces Latin URL | 263.156 | 268.218 | 67,304 / `7234ed860a9cc83045413c4faee63c960a8f2d1917adcf728119307d56e0d783` |
| 4 → 3 | Same Inter Latin URL, distinct native request | 268.015 | 268.218 | 48,532 / `acc60d454f46f2ba233c516aa3299aa60e1f49ffd0f06b8392a7c772a5694087` |

All three request receipts began at 260.812, use GET/font, have status 200, MIME font/woff2, finished terminals and successful continuation attempts. Every retained body rehashes to its native receipt, has `wOF2` magic and a matching declared header length. Total retained font bytes are **164,368**. Requests 2 and 4 are distinct transactions with identical URL/bytes; they were not collapsed into one receipt.

The corresponding host request-receipt-to-continuation intervals are **2.281**, **2.344** and **7.203 seconds**. The fixed 2,000 ms observation window is not evidence that every individual request was continued after exactly two seconds. The continuation attempts have invocation timestamps and returned booleans, but no separate return timestamp; the 4.859-second interval before request 4's continuation cannot be allocated uniquely to an earlier continue call or host scheduling. All transactions nevertheless completed within the source's recorded settlement/custody process.

## 6. Demanded faces, text styles and media receipts

The three demonstrated loading→loaded faces are observer ID **3** (Fraunces, normal, weight 400–700), **10** (Inter, normal, 400), and **24** (Inter, normal, 600), all Latin descriptors with `font-display: swap`. Their family, style, weight, Unicode ranges and resource URLs match the exact retained CSS declarations. All receive `loadingdone` dispatch at page 20,928 ms and deferred receipts at 21,030 ms. Settlement records zero pending deferred receipts, no lifecycle errors and no loadingerror. The other **21 declared faces remain unloaded** and are not required merely because they were declared.

Relevant computed candidate styles are stable across the five phase reads:

| Text surface | Candidate family/style |
|---|---|
| Isha (`.cn`), `05:00` (`.nt`) | Fraunces then Georgia/Times/serif; normal, 600; 30 px / 46 px |
| Fajr in countdown | Fraunces then existing serif fallbacks; normal, 600, 20.25 px |
| `4h 30m` duration | ui-monospace/SFMono-Regular/Menlo/Consolas/monospace; normal, 500, 17.25 px |
| `left` and `until` labels | Inter then existing system fallbacks; normal, 400, 17.25 px |
| Prayer rows | Inter fallback list; names 600 except highlighted Fajr 700; times 600; 12.5 px |
| Location `NewYork` | System-ui fallback list; normal, 400, 11 px |
| Gregorian/Hijri footer | Inter fallback list; normal, 400, 11.5 px |

The `.left` container's monospace family does not describe its Inter label and Fraunces prayer-name children. CSS, computed candidates, actual demand, matching binary custody and loaded faces are joined here without claiming per-glyph native font selection. Two same-URL Inter requests cannot be distinguished as “this one is 400, that one is 600” from URL/body identity alone. Footer and child geometry change after fonts (for example Gregorian width 78.6333→96.3500 px and the Fajr countdown child 43.2167→38.9667 px), while the card remains 325×530. Geometry/text presence does not prove continuous readability.

Before CSS, `fonts.status=loaded` and observer `settled=true` coexist with **zero faces**. The same empty state in fallback is not proof of applied optional fonts.

The media observer installed at page **12,874 ms**, with original media `print`. It retained two mutations: print→all, then all→all, both delivered at **13,615 ms** in separate callback batches. The first has activation upper bound 13,615; the second has none. Two trusted original-link load events at that timestamp record media-at-dispatch `print` then `all`; applied observations use the latest trusted terminal with current connected link `all`. Those are observed delivery/terminal bounds, not attribute-write instants. Media close reports installed/closed/disconnected true, no first/secondary/additional errors.

**No exact video/page/host origin exists.** Both traces explicitly retain `offset=null`, `UNKNOWN_NO_FRAME_ALIGNMENT`. This report does not align the media mutation, request/response, face completion or phase reads to an exact loss/restoration frame. Independent pixel findings remain a separate authority and do not complete the missing fallback arm.

## 7. Primary failure, secondary effects and cleanup

| Scope | Received result and limit |
|---|---|
| Baseline primary acquisition | No exception; literal source assertions match. The ordinal mismatch remains an explicit presentation limitation. |
| Fallback primary acquisition | `case-actions`, action 3 release, Error with externally supplied message intentionally omitted. Original body deadline fire/abort is recorded; font ingress is unstarted. |
| Fallback CSS `failed` terminal | Request 1 was held from 280.859; cleanup abort invoked 291.593 and returned, failed terminal 291.609, final disposition aborted. This is expected cleanup of an unrealized request, not a primary CSS service failure. No response or CSS body exists. |
| Helper errors/secondary failures | Both helpers record `errors=[]` and close `CLOSED`. No `secondaryFailures`, `failureCapture` or `failureCaptureError` are recorded. Baseline has pageErrors=[] and unexpected=[]. Fallback's raw failure export omits the separately collected pageErrors list; its absence is not a proof that no page error occurred. |
| Native ownership cleanup | In each case context.close, browser.close, playwright.stop, server.shutdown, server.server_close and thread.join returned with no recorded error; nativeCleanupEstablished=true. Source thread.join additionally checks that the server thread is no longer alive. |
| Collector setup wording | Fallback nativeSetupEstablished=false is a conjunction requiring populated render/checkpoint/final export evidence; engineSetupFailed=false. It must not be recast as failed dependency installation or failure to launch Firefox. |

The baseline experiment finalized with four native requests, completed CSS/body custody, settled demanded faces, post-tail check and clean close. Fallback has no media observer installation/close because the ingress run never began; its routing ownership was still cleaned up. No cleanup failure or native producer timeout displaced the primary failure.

## 8. Comparison decision and minimum supported next action

**The receiving prerequisite for paired causation fails.** Baseline delivered CSS hash is known; fallback delivered CSS hash/body/native response/trusted application are absent. Neither exact CSS equality nor a separately hash-bound semantic-equivalence disposition can be established against a nonexistent second delivery. Equal requested URLs, browser identity, recipe values or empty font counts cannot substitute. The fallback also lacks original actions 4–6 and the readably populated pre-ingress/intervention phases. This is an **unrealized comparison**, not baseline-only/fallback-only/both/neither evidence.

The minimum evidence-supported diagnosis is a **lost pre-ingress original body prerequisite with an unresolved host timing region**. Source evidence shows the original product deadline operating and the fixture removing an aborted held body. It does not show wrong next-event/date/epoch/countdown logic, a required-face error, changed recipe, broken native CSS custody, failed cleanup or a product-owner defect that warrants a repair. The baseline visual witness, if independently received, remains a new witness for that baseline occurrence; it cannot establish family dependence or reattribute the historical 23 partial-text intervals without the missing comparator.

Root should retain the exact failure and the partial comparison disposition, together with the independent original pixel review, and end automatic repetition. There is no supported automatic native rerun, font-service suppression, deadline/tolerance change, fixture release after expiry, substituted stimulus or renderer/provider campaign.

If root chooses a later bounded diagnostic change, the smallest relevant observability work is to bracket the **existing action-2 sleep/dispatch region** and retain safe structured prerequisite state at a failed release (pending-key presence and the already owned attempt/timer state), without preserving arbitrary external error text. That would locate the still-unknown gap; it would not repair this original acquisition or by itself justify another run. The requested 250 ms sleep, original 10-second body deadline, seven-action sequence, source oracles, cache/routing conditions and original readability requirements must remain intact. No such change or execution is performed or authorized by this report.

## 9. Review commands, artifacts and remaining limits

The final fresh check was executed successfully as:

```text
PYTHONDONTWRITEBYTECODE=1 python /workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/receive_original.py
```

The script performs file/ZIP/JSON/hash parsing plus `git show 4bac6a4781fce62f08ab550a20fe5234d3ebb746:<each bound path>`. It imports no product or harness module and runs no tests, server, browser, workflow or acquisition. Output: 40 exact archive members/no extras; 150 matching source hashes; bound/published/FUSE case equality; baseline literal oracle checks match; fallback oracle checks unrealized; all baseline font body bindings match; phase counts 5/0; native cleanup receipts true/true.

Additional read-only inspection used `git cat-file -p <exact commit>`, `git diff-tree --no-commit-id --name-only -r <exact commit>`, `rg` and `sed` over exact source copies, and Python projections of the original setup/producer/trace files. Root's candidate manifest and r2 source review were hash-checked for code provenance. An optional fontTools WOFF2 metadata decode was unavailable because the installed runtime lacks Brotli; no dependency was installed and no decoded name/axis/glyph claim is made. Native body hashes, WOFF2 headers and exact CSS descriptors were verified separately.

Useful derived files:

- [receive_original.py](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/receive_original.py): reproducible read-only input analysis.
- [read-analysis.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/read-analysis.json): full command arrays, source bindings, action/timer/oracle/request/phase projections.
- [native-receipt-projection.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/native-receipt-projection.json): complete named text styles, face and media receipts with snapshot projection.
- [css-font-byte-metadata.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/css-font-byte-metadata.json): exact CSS descriptor parsing and binary-decoding limitation.
- [candidate-provenance-checks.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-ingress-source-receiving/candidate-provenance-checks.json): published-tree/manifest join only.
- [font_ingress_source_receiving.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/reviews/font_ingress_source_receiving.json): structured final findings and evidence digests.

No secrets or credentials were inspected. External/repository text was treated as data; no prompt-injection instruction was followed or found in the scoped reviewed material. Intentional writes were restricted to this report pair and `recovery/font-ingress-source-receiving/`. No hidden commit, push, tag, release, merge, publication, provenance assertion, product/harness/test edit, native replay or broader acceptance claim was made.
