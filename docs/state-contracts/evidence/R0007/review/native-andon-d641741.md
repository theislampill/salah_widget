# R0007 bounded native-launch Andon diagnosis

## Entry, identity and authority boundary

This report answers the explicit direct-entry audit-Andon cord pull from `/root`. The observed abnormality is the first private native acquisition ending before browser setup. The requested scope is read-only diagnosis of that failure, a justified next execution surface, and recipe/adjudication hazards relevant to the required native run. The caller retains all source, execution, currentness, lifecycle, publication, acceptance and closure authority.

Reviewed immutable candidate: **`d641741df1397659da6ef817fa41aa975f7f3930`**, tree **`ce00619ac4821469647cf3f5ff905e82936a7688`**. Repository sources below were read with `git show` at that commit because the caller advised that source fixes would proceed concurrently. This report does not qualify subsequent edits.

Retained acquisition: `/workspace/scratch/8726e3e6def5/r0007-native/r0007-native-gutavy3z`.

The only written output of this work is this requested ignored report. No browser was launched; no source, recipe, workflow, canonical audit state, credential, sibling branch or protection was changed. No workflow was invoked. No child was routed. The caller's statement that the launch intent was closed at matching identities and `chain.done` verified is **caller-provided context**, not a currentness/closure claim independently issued here. This report grants no PASS, release, native acceptance or AUDIT_COMPLETE.

## Disposition

**The retained failure is a local native-launch/setup abnormality, not evidence of an R0007 application failure.** Chromium aborted at its process-singleton socket setup before the driver created a browser context, navigated to the instrumented document, or observed a product render. The appropriately bounded countermeasure is to retain this failed acquisition and use the commissioned R0007 Windows workflow on its own branch after the caller has completed and bound the corrected candidate and qualification repairs. Do not try to make this restricted local process succeed by disabling browser sandbox/security or borrowing R0017's host/workflow.

Separately, the immutable candidate contains two concrete adjudication defects and a capture-handling hazard that should be resolved or explicitly bounded before relying on the next acquisition. They are described below. The current failed attempt is already rejected; the defects did not convert it into accepted source assertions.

## Observed evidence and bounded causal account

The acquisition summary selects only `chromium / NE07-reordered24`. It records Linux `6.18.57`, Python `3.12.14`, Node `v24.22.1`, Playwright `1.62.0`, the commit/tree above, `selectedSourceAssertionsMet: false`, and exit code `1`.

The actual producer record has `launched: true`, `terminalState: "exited"`, and `exitCode: 1`, from `2026-11-10T01:55:05.019868+00:00` through `01:55:06.631709+00:00`. The browser log reports:

```text
FATAL:chrome/browser/process_singleton_posix.cc:297
Check failed: . socket() failed: Operation not permitted (1)
ERROR:third_party/crashpad/crashpad/util/linux/scoped_ptrace_attach.cc:27
ptrace: Operation not permitted (1)
<process did exit: exitCode=null, signal=SIGABRT>
```

The consumer trace has `actions: []`, `snapshots: []`, and `captureMismatches: []`; there is no browser identity, PNG or WebM. Its failure is `TargetClosedError` at `BrowserType.launch`. Its failure-capture attempt encounters `frame is None`. The wrapper had already produced instrumented-document hashes before launch; those hashes show preparation, not browser execution. The driver's order is unambiguous: launch at `tools/cp9/r0007_browser.py:200`, create context/page at 201–202, navigate at 229–235, record browser identity at 236, then enter case actions at 237.

The admissible causal conclusion stops at a launch-surface permission denial. The fatal singleton socket error is the first observed startup failure. The crashpad `ptrace` denial follows that fatal error and is consistent with failure of crash handling; the evidence does not make it a separate application cause. This review did not determine which host enforcement mechanism produced EPERM, and does not claim that all socket operations are unavailable. The Python local server had been established before launch. No model, renderer, ingress, endpoint/date, or recipe assertion had executed in the browser.

The retained adjudication correctly records `accepted: false`, `nativeSetupEstablished: false`, and `OBSERVATION_NOT_ACCEPTED`. It also records `cleanupEstablished: true`, which in this version means a matching consumer-summary receipt exists; it is not an independent process-tree proof. The producer exit and browser-exit log are the actual terminal observations available here. The governor's stronger launch/cleanup/currentness receipts remain outside this report's authority.

**Local versus systemic:** the triggering incident is local to this launch surface. Repeating the same acquisition there without a supported environmental change is unlikely to add product evidence. The adjudicator findings below are systemic within the qualification helper: they can affect any selected case, independent of R0007 product correctness. The two endpoint/date source defects mentioned by the caller are owned by the parallel source reviewer and are not attributed to this launch failure.

## Findings that can distort or waste the required acquisition

### NQ-1 — Acceptance does not require the collector's own cleanup/final-summary predicate

**Confirmed checker defect; fix before relying on the collector's aggregate success.**

`tools/qualification/r0007_native.py:190` computes `cleanupEstablished` from one matching final summary receipt. Healthy acceptance at 202 and mutant acceptance at 212–214 do not require that predicate. The loop sets `stopped` from it at 299, but the final aggregate at 304–307 can still succeed if this is the last or sole planned result: all recorded results can have `accepted: true`, with no unattempted cells, while the final result has `cleanupEstablished: false`.

A purely in-memory diagnostic invocation of the exact immutable `adjudicate` function reproduced this. No filesystem evidence was created or changed for the probe and no browser, process producer, product code or workflow was run. A fake path provider supplied a normal-looking source-assertion trace, matching source/fixture hashes, an identity file, and `summary: {"receipts": []}`. The result was:

```json
{
  "accepted": true,
  "status": "SOURCE_ASSERTIONS_MET_PIXELS_PENDING",
  "cleanupEstablished": false,
  "nativeSetupEstablished": true,
  "firstPresentationAssociation": "RECORDED_REQUIRES_PIXEL_REVIEW"
}
```

This is a counterexample to checker logic, **not native evidence** and not a claim that the retained actual summary is malformed. Recommended repair: make accepted healthy and mutant outcomes require the matching terminal summary/cleanup predicate, validate the final receipt's status against its trace, and make the final aggregate fail closed on any unresolved terminal condition. Preserve the existing exact mutant failure/healthy-control checks. A small pure adjudicator regression for missing/mismatched summaries is proportionate; no native rerun is required to demonstrate this particular repair.

### NQ-2 — “First presentation recorded” is inferred from absence of mismatch records

**Confirmed evidence-status defect; it must not be used to credit first recovery pixels.**

`tools/qualification/r0007_native.py:204` emits `RECORDED_REQUIRES_PIXEL_REVIEW` whenever `captureMismatches` is empty. The retained no-browser failure itself contains this value despite having no capture, browser, render or video. Thus the value does not establish that any presentation was recorded.

For healthy `NE07-recovery24`, `NE07-recovery12` and `NE07-dst-recovery24`, the recovery capture is `after-next-settlement` with `firstRender: false` after a fixed 250 ms scheduling observation. The runner selects the latest retained render for that capture (`tools/cp9/r0007_browser.py:278`) and checks ordinal association only for `firstRender` captures (308–312). Consequently an empty mismatch list in these cases says nothing about whether the recovery capture is the first eligible render or the first presented recovery frame. The unavailable capture's association cannot serve as the recovery capture's association.

The recipe already states this limitation correctly at `execution.firstFrameConstraint` and `execution.recoveryConstraint` (JSON lines 90–91), and the normative ledger's 7.07, A05 and ES07-06 retain the earliest eligible dirty-frame obligation. The dangerous step would be promoting the summary field, a 250 ms wait, or an eventual still into acceptance.

Recommended repair: report presentation obligations per named capture and derive their status from actual capture/presentation artifacts and ordinals. Missing capture or absent browser setup is unverified. A latest-render recovery capture remains eventual-state evidence unless separately associated with the earliest eligible receipt and actual native video. Keep independent pixel review mandatory even when all ordinals match.

For the next acquisition, the reviewer must bind the actual held reply's settlement/adoption to the earliest eligible completed render, verify the unchanged frozen accepted epoch, examine all intervening receipts and video frames, and identify the first presented recovered surface. If that evidence cannot distinguish the next eligible opportunity from a later incidental redraw, keep the first-frame obligation open. Do not wait for the expected key/clock, call `render`, advance the fixture clock, or add a substitute scheduler to obtain a favorable image.

### NQ-3 — First-capture mismatch handling depends on a capture's literal name

**Confirmed control-flow hazard; its occurrence on Windows is not yet observed.**

The runner appends an ordinal mismatch but continues only if `action["name"] == "first-current"`; every other first capture raises immediately (`tools/cp9/r0007_browser.py:308–312`). All present/missing/recovery recipes take an initial `unavailable` capture with `firstRender: true` before releasing tomorrow. If a legitimate later product render exists before or during that screenshot, the historical earliest unavailable receipt and current still will differ, causing the case to abort before recovery is exercised. The code comment says to preserve mismatches and continue collecting video/oracles, while the implementation applies that policy only to one name.

A legitimate source of additional frozen renders exists: relevant font completion/error sets `_renderDirty` (`src/native/index.html:3208–3228`). Other native asynchronous preparation can also be present. This establishes a plausible path, not a claim that such a race occurred in the failed launch. The two initial `wait` actions and screenshot protocol round trips do not guarantee that the first current receipt remains the latest receipt.

Recommended bounded handling: preserve a failed still association as an explicit presentation failure/pending review while continuing the intended acquisition and source assertions when safe. Apply the chosen policy to the capture's declared obligation, not its spelling. A video-only run still needs the same honest earliest-frame review; changing output mode does not cure or waive a historical ordinal mismatch. Retain mismatch evidence and avoid restarting the whole native matrix solely to obtain a lucky still.

### NQ-4 — Browser identity is not exact enough under the planned workflow

**Confirmed binding limitation.**

The workflow clears `SALAH_BROWSER_EXECUTABLE` and installs managed Chromium/Firefox. `tools/cp9/browser_runtime.py:27–28` then records the generic string `explicit system chromium if available; otherwise Playwright managed engine` as `executable`, rather than the actual selected executable. That string is especially imprecise for Firefox. The wrapper's setup predicate merely tests that `browser-identity.json` exists (`r0007_native.py:191–198`), without parsing or checking requested engine/actual family or platform.

The ledger and recipe binding instructions require actual OS/browser executable/version and environment attribution. Record the resolved browser executable actually selected, browser family/version, OS, headless/headed state and the relevant sandbox request. Validate identity structure and requested engine in adjudication; retain actual Windows metadata in the acquisition summary. These are reporting/validation changes and do not require disabling protection or touching an owner browser profile. Native launch success and browser version remain facts to obtain on the Windows host, not facts inferred from workflow YAML.

### Scope checks for the final reviewer

These are limits to map explicitly, not newly invented product requirements:

- `NE07-reordered-offline` selects generated `offline.html`, but has no `offline: true`; the actual nonlocal-network-abort route at `r0007_browser.py:203–217` is therefore not activated. The case can qualify the generated offline entry's selected-target consumer. It cannot by its name establish a real network-disconnected scenario. If the surviving original row requires that scenario, explicitly exercise that existing route or retain the gap.
- The defaults contain 17 healthy cells; `--include-mutants` adds nine mutants. The four named Moon/motion preservation cases are conditional and omitted from this invocation. Their omission is permitted only with the ledger's exact protected-owner/caller/input/environment reuse adjudication; they must not disappear from the denominator because the launcher exits zero.
- The matrix includes spring 24/12 h, fall 24 h, ordinary 24 h, and UTC recovery 24/12 h, plus DST recovery 24 h. Do not describe it as every historic DST case in both formats. The final whole-contract reviewer must explicitly map the surviving A04/A05 requirements and unchanged format claims; this report does not grant an exception or demand an unscoped full cross-product.
- `comparisonRequirements` describes real SVG/crop pairs, but `check_expected` does not execute cross-case equality or visual review. Preserve an explicit review result for spring/fall/ordinary interval-only pairs and for the selected marker/row. Driver success is source assertions only.
- Mutants require named healthy controls and exact intended `AssertionError` substrings, and those relevant discriminating fields are ordered first in their expectations. No concrete signature-order defect was found in the reviewed recipes. Keep that protection after source fixes; generic exit 1, anchor failure, setup failure or missing snapshots must remain rejected.

## Recommended countermeasure and safe next execution surface

1. Retain this failed acquisition and its unaccepted status. Do not reclassify it as an application regression or mutation rejection, and do not repeatedly retry the unchanged restricted local launch route.
2. Let the caller finish the separately owned endpoint/date fixes, generate the delivered entries, and resolve the bounded adjudicator/capture/identity findings above. Use exact final source/recipe/fixture/driver hashes for the subsequent acquisition. This report's commit binding must not be reused as a claim about those new bytes.
3. Use the existing **R0007-owned Windows workflow** at the reviewed candidate's `.github/workflows/r0007-native.yml`, subject to the caller's normal publication/execution controls. It targets `windows-2022`, checks out `${{ github.sha }}`, disables persisted checkout credentials, pins Playwright 1.62.0, installs Chromium and Firefox in private runner paths, runs the collector serially with `--headed --include-mutants`, and retains setup outcomes and raw artifacts with `if: always()`. This matches the mandatory Windows/two-engine frontier in the ledger without weakening the local sandbox or claiming a sibling's resources.
4. The workflow is push-triggered only for the R0007 branch and workflow/request-file paths. Source-only pushes do not necessarily request a new run. At the reviewed commit the named request file is not present. The caller should use the supported own-branch trigger/transport and bind the resulting run's actual SHA; do not assume workflow presence means execution. The separate transport investigator owns that question. No dispatch, push or workflow effect is performed or authorized by this report.
5. Inspect the first supported-host outcome before spending additional runs. If the host again cannot establish browser setup, retain the failure and classify the remaining cells as unattempted for that unchanged failure mode rather than replaying identical setup failures. Distinct engines remain independently required; one engine's result does not substitute for the other.
6. Complete independent actual-pixel and first-recovery review at the final relevant identities. Apply only the small scoped preservation control if exact reuse fails. Reconcile accepted preceding R0017 main before final R0007 acceptance, then preserve the required merge order **R0017 → R0007 → R000B** and the exact owner merge-approval gate.

The workflow is a justified *next surface*, not a demonstrated available browser or a successful native run. Its future dependency installation, launcher success, actual OS/engine identity, cleanup and evidence readback remain observations to obtain.

## Escalation recommendation and follow-up evidence obligation

**Escalation recommendation:** return this diagnosis to `/root` for a bounded qualification-mechanism repair and the commissioned own-branch Windows acquisition. Do not escalate into product/clock/inverse changes to address the launch error. Do not seek a security-bypass exception. An entitled-owner platform amendment is an alternative only if the required Windows acquisition truly remains unavailable; no such amendment is granted or needed by this report to continue the already commissioned engineering.

The root/caller should retain the failed attempt, the exact repaired candidate and recipe identities, pure checker regression evidence for NQ-1/NQ-2, the actual Windows workflow/run identity and setup/producer exits, both browser identities, complete traces and original presentation artifacts, and independently attributed first-frame/geometry/SVG/preservation dispositions. Any remaining setup, first-presentation or coverage uncertainty must stay explicit in the existing acceptance ledger. A ready source tree or a collector exit zero is insufficient for whole-owner acceptance.

**Hansei / recurrence control:** separate launch capability, source assertion results, terminal cleanup, and native presentation association in the evidence schema. The observed failure usefully exposed an empty-mismatch default that looked more affirmative than its evidence. Require positive evidence for each field and fail closed on missing terminal summaries. Keep those small diagnostics at the mechanism boundary so future runs do not need another native attempt to rediscover the same bookkeeping error.

## Exact proposed repair and verification scope for a separately commissioned engineer

The following is a proposal, not implementation or acceptance. Keep it within the R0007 collector/observer and the smallest shared browser-identity interface necessary; coordinate any shared-file change with the caller. The caller has now reported new endpoint/date source fixes and generated outputs. Rebind these repairs/tests to that new candidate when commissioned; the findings above remain evidence about the reviewed immutable commit.

### Collector terminal gate

In `adjudicate`, define one explicit valid-final-summary predicate: exactly one receipt, the selected `caseId`, a receipt status matching the retained trace, and the expected terminal summary form. Preserve `cleanupEstablished` as a separate disclosed field. Require that predicate in both healthy and intended-mutant `accepted` branches. At the outer aggregate, require every accepted result to have established terminal cleanup as well; a sole or last result with failed cleanup must not produce zero exit. Do not infer OS-wide cleanup from the summary name; retain actual producer terminal evidence and the caller's process-ownership controls.

### Presentation evidence states

Replace the empty-mismatch default with a per-capture evidence assessment. A small explicit state vocabulary could be:

- `UNVERIFIED_NO_NATIVE_SETUP`: browser setup/render evidence absent. This is the required disposition for the retained launch failure, irrespective of an empty mismatch array.
- `UNVERIFIED_NO_CAPTURE_ARTIFACT`: setup exists but the declared capture/presentation receipt or original native recording is absent.
- `UNVERIFIED_ORDINAL_MISMATCH`: the named first-render association does not bind the receipt to the capture. Preserve all before/after/receipt ordinals.
- `EVENTUAL_STATE_ONLY`: a recovery capture intentionally uses the latest render and does not claim earliest presentation.
- `RECORDED_PENDING_INDEPENDENT_REVIEW`: the declared association is positively recorded with the required artifacts; this still grants no first-pixel or visual acceptance.

Keep `firstFrameAcceptance` unverified/pending independent review for all automatic results. Store capture names, their declared first/eventual obligation, receipt ordinals, before/after ordinals, and actual artifact identities. Never promote the unavailable capture's association to the recovery capture. Retain the recipe's expected outputs unchanged. On any first-capture mismatch, append the mismatch and continue actual acquisition/source assertions instead of raising solely because the name differs from `first-current`. No manual rendering, expected-target wait, clock adjustment or extra product timer is needed.

### Executable binding

Resolve the executable selected for the requested engine before launch: the explicit executable override, the selected system Chromium path, or the selected Playwright engine's managed executable path. Record that concrete path with a selection-kind field, requested engine, actual engine family, actual browser version, OS/machine and headed/headless state. Preserve `chromium_sandbox=True` and current security policy. Pass the expected engine into collector adjudication and parse/validate identity content; file existence and the generic fallback sentence are insufficient. The wrapper's actual OS record and any mandatory Windows scope check should be compared explicitly, without claiming that a requested platform proves the actual platform.

### Minimal discriminating tests

All tests below can use in-memory evidence fixtures or temporary disposable test directories and browser/playwright stubs. They must not launch a browser or touch profiles. They test evidence logic, not native pixels.

| Test | Input / action | Required result |
|---|---|---|
| Q01 healthy terminal positive | Healthy trace, real-render-shaped receipt, matching hashes/identity, producer exited 0, one matching final summary receipt/status | Source assertions accepted; cleanup established; pixels/first frame still pending. |
| Q02 missing summary | Same positive data with no final summary | `accepted=false`; no zero aggregate; cleanup unverified. |
| Q03 malformed/mismatched summary | Independently replace receipt list with empty/two entries, wrong case ID, or status contradicting trace | Each is rejected; do not conflate the failed summary with a product failure. |
| Q04 last-cell/sole-cell cleanup failure | Feed the final aggregator a sole/last result whose source-assertion fields look successful but cleanup is false | Aggregate selected-source success false and nonzero result; no silent success at the end of the loop. |
| Q05 mutant terminal discrimination | Valid named healthy controls plus intended assertion/exit 1; then invalidate final summary or make exit/substring/variant unrelated | Only the valid terminal intended assertion gets source mutation credit; every invalid variation is rejected. |
| Q06 retained no-browser shape | `actions=[]`, `snapshots=[]`, no identity/capture/video, `captureMismatches=[]`, launch exception | Setup false, accepted false, first presentation `UNVERIFIED_NO_NATIVE_SETUP`; never any recorded/presented state. |
| Q07 empty mismatch is insufficient | Valid setup with no capture artifact, then with an `after-next-settlement` latest-render capture | First case is missing-artifact unverified; second is eventual-state only; neither proves first recovery pixels. |
| Q08 first-capture mismatch continuation | Stub consecutive ordinals around an `unavailable` first capture, then around `first-current` | Both retain mismatch and continue subsequent actions/export; neither receives first-frame acceptance. The behavior does not depend on the literal name. |
| Q09 positive ordinal association | Matching named first capture with before=after=receipt ordinal and retained artifact identities | Association recorded pending independent review; automatic first-frame/pixel acceptance remains absent. |
| Q10 exact executable selection | Stub explicit override, system Chromium discovery, and managed Chromium/Firefox executable paths | Each identity records the actual resolved selected path and correct family/version; no generic fallback phrase. Sandbox request remains enabled for Chromium. |
| Q11 malformed identity | Missing/empty/invalid identity JSON, requested/actual engine mismatch, or generic/unresolved executable field | Setup/identity binding rejected; do not credit the other requested engine. |

After these pure controls and exact fixture binding are valid, obtain the new native observations through the caller-owned Windows route. The independent reviewer must still adjudicate the first visible recovery from original trace/video and all intervening frames. No test above substitutes for that obligation.

## Evidence hashes

All acquired-file paths in the first table are relative to the retained acquisition root above.

| Evidence | SHA-256 |
|---|---|
| `summary.json` | `2d3391871779b1b8c00ab1f43bd23b247a7622c86dc8b614b07dd2a5614055d1` |
| `bound-cases.json` | `5f1a4e8fecda4408b0b986aeeb5df12ab0ffa283d74c02eb4920c728a2dee3f3` |
| `capacity-lease.json` | `73184d3c2439bb21c05626a728f06bfd9f7166958ba02af45e7b4e4d97acf1a5` |
| `chromium/NE07-reordered24/attempt-0001/producer.json` | `799cf232d6a717bc0657459c85069f44671867b7bb7a29dc75f97b8f85032d6b` |
| `chromium/NE07-reordered24/attempt-0001/producer.log` | `062cbb8a025c0227b32da1cace4bf3194e4dd4043727b709a0bdbb9ea7e1a2e1` |
| `chromium/NE07-reordered24/attempt-0001/adjudication.json` | `106ad31af8cc89bcf4eba75135b20e7b702d40c782bd78c1db19fceadcdd4fa8` |
| `chromium/NE07-reordered24/attempt-0001/consumer/summary.json` | `3dc549965ce77d2be1385bbace21631493fa156fb8bb1185a4b540d7f893d8f3` |
| `chromium/NE07-reordered24/attempt-0001/consumer/NE07-reordered24/trace.json` | `7626e03203ccd7889ecd41aebfc9568bd16bdd554b0caca69ff125f02adfbecb` |

All source paths below are bound to immutable commit `d641741df1397659da6ef817fa41aa975f7f3930`.

| Source | SHA-256 |
|---|---|
| `tests/rlgwo/R0007-next-event-recipes.json` | `3cff0cb5afe9544dd23fb7149b747856d5b99257f60911a0ce86d961d5291c0e` |
| `tools/qualification/r0007_native.py` | `7689b9d4423f056838f2113477d5b588a179992a341e11f3cf5d4806d089d104` |
| `tools/cp9/r0007_browser.py` | `df8d23875aa689364ac394bccfece57019efb698875a208269e8755dd317fbc3` |
| `tests/rlgwo/prayer-browser-fixture.cjs` | `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f` |
| `tools/cp9/browser_runtime.py` | `af7e6376ac8fe3c731ea1e215dac37faadc48f1f766a6bdf32637426e1daa4e0` |
| `.github/workflows/r0007-native.yml` | `ea35865b32441417bbb78f262870fda70324fc0497f48f422be37638b7f44252` |
| `docs/state-contracts/R0007.md` | `7c2d577cbe1fbdd9d4fe2c7c504e19be1de857a2fd10192208608c29f14604ba` |
| `docs/state-contracts/evidence/R0007/acceptance-ledger.md` | `85c533d8f9e029e9c9f7172ffb84ac4158ac7f27352c21c4a5335f9e4b7a9235` |
