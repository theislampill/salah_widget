# R003F opt-in hosted diagnostics

## Scope and preserved boundaries

This source integration connects two independently reviewed leaves to the hosted
coordinator. It adds no product change and selects no new native campaign. The
checked-in campaign remains byte-identical to the reviewed R002F-only Chromium
DPR1 tab-hide selection at `0c7c59810036b874d6e423d358d836162b76e4ec`.
Its SHA-256 is `496a769675733d9e8e26d9a211c0a53028557b8b1ce852e85fd8bf4ecfdbda3c`.
The source controls for these two routes do not select either for execution;
any later campaign-only activation requires its own exact-source review.
The original Firefox failure, WebKit preconnect failure, human judgments and all
R003F owner gates remain unchanged.

The Firefox leaf is imported byte-for-byte from
`276e63b57f9e40b137fa528273c980e1351548dc`; its complete source-manifest digest is
`4221060e1613f913b157f0c326cfeefc0f0661ff156d2ce5eac51f9c44b992ef`.
The WebKit leaf is imported byte-for-byte from
`06f1ad3fc7e418e0e2f1ad33afb4f692dabc82f0`; its complete deterministic derived
source receipt is
`c8c26bfdff9f20b38a5ece423db2759fc96339ca9d68cf2c68f7893d36930290`.
The original proxy, Node guard, UI predicates, calendar-light Andon, physical
reference and original capture driver remain unchanged. The derived WebKit
driver comes only from its guarded source materializer.

See the unchanged leaf contracts
[Firefox policy](../../tools/qa/hosted-native/FIREFOX_POLICY.md) and
[WebKit document input](../../tools/qa/hosted-native/R003F_PRECONNECT_INPUT.md).
Neither leaf provides original B0, complete-eight matrix, physical, experiential,
human, Safari or device acceptance. There is no new rendering or transition
fidelity claim. Existing screenshot and clip gates remain required.

## Exact selection and output types

Each selection requires only `workOrders: ["R003F"]`, DPR1 and its one engine.
Generic retention, matrix selection, star diagnostics and supplemental route
compositions are refused. The same value is used by `campaign.json`'s
`r003fHarness` and the planner/coordinator `--r003f-harness` option.

| Selector | Engine | Lane id | Result kind | Successful diagnostic status |
|---|---|---|---|---|
| `firefox-policy` | Firefox | `r003f-firefox-policy` | `r003f-firefox-policy` | `OBSERVED_FIREFOX_POLICY` |
| `preconnect-input` | WebKit | `r003f-webkit-preconnect-input` | `r003f-preconnect-input` | `OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC` |

The first qualifies only `MANAGED_POLICY_DIAGNOSTIC_ONLY`, with timing class
`instrumented-managed-policy-dwell`; the second qualifies only
`ALTERED_INPUT_DIAGNOSTIC_ONLY`, with timing class
`instrumented-altered-document-input`. Both carry
`nativeProductAcceptance: NOT_EVALUATED`, `humanAcceptance: OUTSTANDING`,
`originalFailedObservation: UNCHANGED` and `boundaryEngine: chromium`.
The new statuses are not aliases of `PASS`, original B0 or complete-eight intake.

## Actual launch order and policy ownership

The unchanged acquisition installs Chromium for the shared boundary control,
plus the selected Firefox or WebKit engine. The shared boundary driver is
explicitly Chromium; it is never described as a Firefox startup observation.

1. The preparation namespace performs the original kernel checks and Chromium
   browser boundary control. Its real receipt and sibling report/streams remain
   at `capture/isolation/preparation`.
2. The unchanged common preparer runs using the acquired Python. The coordinator
   records its actual command, source, process and original preparation namespace.
3. A separate bounded diagnostic preparation records actual Python and Node
   commands and exact child streams. Firefox checks current acquisition and
   reviewed source without importing Playwright or creating a policy. WebKit
   runs its unchanged materializer, then checks the complete eight-file closure,
   actual original index, current packages, browser descriptor and executables.
   Its acquired Playwright import only resolves the WebKit executable path.
4. The planner and outer coordinator independently re-admit current complete
   source/preparation custody. Missing or failed preparation produces an empty
   command and a blocked row; no other harness is substituted.
5. The fresh lane namespace repeats the original kernel and Chromium boundary
   controls. Current-source admission runs again before the diagnostic entry.
6. The unchanged Firefox leaf then rechecks its current namespace and acquired
   installation, performs its no-live-installation census, exclusively creates
   the exact policy, and only then launches this diagnostic Firefox. An existing
   arbitrary or earlier policy is refused. There is no policy installation or
   adoption across the preparation/lane boundary.

The Firefox leaf keeps its original strict launcher/preferences, actual
`about:policies` DOM readbacks and ordinary 60-second driver-clock dwell.
`historicalFirstStartup` remains `NOT_ESTABLISHED`, and `refinedCapture` remains
`NOT_OBSERVED`. This order does not establish the cause of any previous startup
failure. The workflow sparse checkout adds only the two unchanged original
guard files required by the pinned Firefox packet.

## Custody and currentness

The shared Python helper is `r003f_diagnostics.py`. It binds fixed task paths,
independently acquired Python/Node/package paths, actual parent/child commands,
source digests, complete original common preparation, original preparation
namespace and current derived source before optional verifiers run.
`source-only-common-preparation-execution/1` is accepted only for a separate
source-only check; every native plan/readmission requires the genuine original
hosted preparation context. A later lane namespace cannot upgrade that claim.

The complete admission and complete canonical lane are compared, including
output paths, command arguments, environment, mode, scope and budgets. Boolean
zero, copied executable paths, altered helper populations and partial receipts
cannot authorize execution. The original common and optional process records
and streams are retained. Optional child stdout/stderr are stored as their exact
bytes; decoded text is only a process-result view.

After actual entry completion, a separate exclusive process record binds its
actual return code, timeout, command, bound and retained stdout/stderr bytes.
Final intake again checks current source and full preparation. The shared
`r003f_diagnostic_replay.cjs` is invoked as a normal file by the acquired Node,
with no Node flags. This preserves the unchanged Firefox preflight's rejection
of executable-injection flags and environment variables; it is not run with
`node -e`.

Final Firefox intake reads the actual parent/child reports, source/acquisition
records, policy, DOM readbacks, clock interval, census/ownership, lifecycle and
cleanup records, raw network ledger and Node refusals. It recomputes the original
strict network verdict and reuses the unchanged final leaf predicate.

Final WebKit intake checks both retained HTML response bodies, the current
original document, complete derived closure, actual four PNG identities and
dimensions, original UI/scene/light/measurement-completeness predicates, raw
request census and recomputed B0 repeat envelope. The unchanged owner report
does **not** retain the full UI mask or raw proxy ledger. This intake does not
synthesize them or claim complete independent recomputation of all image
metrics or complete-eight verification. Successful actual original driver
completion and its strict final isolation verdict remain prerequisites.

Actual isolation failure retains priority. The WebKit calendar-light fault keeps
its original Andon. Missing bytes, nonzero child completion, source drift,
malformed data and timeout remain incomplete; an unsuccessful outer namespace
cannot promote an inner diagnostic label.

## Explicit uncalibrated ceilings

These are source-selected ceilings, not measured runtime guarantees. The
original waits are unchanged. Real deadline exhaustion or missing evidence
remains incomplete.

| Component, seconds | Firefox policy | WebKit document input |
|---|---:|---:|
| Original common preparation | 900 | 900 |
| Optional preparation parent / child | 180 / 60 | 180 / 60 |
| Source verifier child | 45 | 45 |
| Planner | 120 | 120 |
| Preparation namespace | 1,350 | 1,350 |
| Outer current admission | 120 | 120 |
| Inner current admission | 120 | 120 |
| Native entry | 330, unchanged leaf child 270 | 960, original capture 900 plus document reserve 60 |
| Final intake / final Node child | 90 / 30 | 120 / 60 |
| Namespace allowance | 75 | 75 |
| Complete lane namespace | 615 | 1,275 |
| Accounted campaign allocation | 2,085 | 2,745 |
| Coordinator | 2,640 | 2,880 |
| Workflow observation step | 45 minutes | 49 minutes |

The namespace maximum includes inner admission, entry, final intake and its
allowance; the campaign allocation additionally includes preparation and outer
admission. Actual remaining coordinator time caps each launched namespace.
With 75 seconds or less left, the lane is `NOT_RUN` and has no fabricated process
record. Acquisition, seal and total job ceilings remain unchanged.

## Producer migration and retained evidence

The portable capture caller's terminal gate recognizes each diagnostic only for
its exact selected campaign, lane kind, engine, DPR, canonical task/runtime/
command/budgets and scope. Both inner and outer rows must carry that exact status
and scope, with real integer-zero, untimed namespace completion. Original modes
refuse these new success labels. The diagnostics refuse original `PASS` and each
other's success labels. Completed known failures and genuine `NOT_RUN` records
remain retainable.

For these opt-in routes, the producer started/completed identity also binds the
full new coordinator/replay/leaf/common-helper/guard source closure. An old
source receipt, missing new source member or changed current member is refused;
there is no migration by editing old plaintext or manufacturing a completion.
The portable transport, envelope, original private logical filenames and
historical artifact readers remain unchanged. This is still source-bounded
producer completion within the existing trusted task/checkout custody model;
it is not an atomic snapshot against a same-account concurrent writer.

## Source verification plan

The new registered central suite has 41 Python cases; the new replay suite has
41 Node cases. They exercise real source transformations/verifiers, exact file
retention, real failed/timed child processes, canonical command/currentness
refusals, actual producer-gate coupling and source-bound final replay. Browser,
namespace, acquisition and clock positives are explicitly synthetic doubles.
Some source checks use non-executable synthetic browser files and an executable
path resolver with no browser launch API. They are not native acquisition,
policy-effectiveness, layout, rendering or performance evidence.

The imported Firefox 57-case and WebKit 28-case suites remain byte-identical.
The regression registry records the new instruments and the expanded dependent
source closure in the same change. Original source identities, workflow
selection, guard bytes, transport/envelope bytes and product/generated/vendor
trees are checked separately. A new native observation remains a later,
independently reviewed exact-source execution with its actual bytes and failures.

The [R0028 census clarification](R0028-input-coverage-census.md) permits declared
modules and excluded recipes to remain hashed source inputs without claiming
they execute. Actual argv/covers conflicts and all existing coverage checks
remain failures. It accompanies this source integration because its complete
input closure exposed that distinction.

The first complete diagnostic composition retained all 84 preceding registry
commands and added four distinct diagnostic commands. The later paired PSF
source composition retains all 88 in their original order with all non-input
fields unchanged, appends its separate 34-case command, and adds dependency
inputs to seven shared-caller commands. The two imported leaf command objects
remain exact. The composed central control binds the preserved R002F campaign
bytes explicitly; its earlier B0-specific assertion and actual composition
failure remain retained separately.

The passive R0040, R003F diagnostic and paired PSF selectors keep their separate
budgets and mutual exclusions. The passive runtime, R002F focus-owner source,
pure PSF source experiment and original transport/envelope remain preserved.
The separately admitted [paired PSF caller](R0035-psf-native.md) is present as
opt-in source only. It supplies no R003F admission and does not activate either
foreign-engine diagnostic or replace their current-source requirements.
