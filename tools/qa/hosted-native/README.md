# Hosted native research observations

This opt-in branch runs private research observations for Salah Widget R002F-A2,
R0035, R0040 and R003F. The campaign retains the three already published recipes
and can append the separately reconstructed R002F probe. It does not adopt a
product candidate or supply owner/human acceptance.

## Immutable inputs

| Input | Commit |
|---|---|
| Reviewed research | `55d1b3edb66d2c35679707120b01ee1d3455e4a3` |
| Clean main control | `df644ef60156b67b5c487395176369bcec7a0d7b` |
| Historical rain fixture helper | `4029d2f67f5a880c8ad889443bb7557d96022c45` |

The workflow checks out orchestration at its actual run SHA. Preparation checks
the immutable source identities, reproduces the materialized hashes and performs
two canonical builds with V1 controls. Its receipts stay private. Research and
baseline checkouts retain genuine Git identity; the R0035 main-arm guard is not
replaced with an archive label.

`campaign.json` selects the installed engine, R003F DPR (1 or 2), and whether to
include R002F with its own DPR (1–3), rounds (1–10) and section (`all`, `prayer` or
`preview`). The initial R002F integration uses Chromium, DPR1, one round and both
sections. Those controls do not change the original R0040/R0035 drivers' fixed
DPR1 or their existing recipe arguments. The validated campaign is retained
privately with the observations.

### Conditional campaign selection and evidence retention

The checked-in follow-up selects one revised R0040 Chromium capture on genuine
main (`bday`, `moderate`, `M1`, common dispersion), corrected R003F B0 at DPR2,
then R002F DPR1 for five rounds of prayer restoration only. The rain capture always uses its reviewed
final-state wrapper; generic evidence retention remains disabled. Previous
option-cell, lunar, star and preview results remain separate, unchanged evidence.
Campaigns can set these optional fields after the preceding evidence has been
inspected:

| Field | Allowed value and effect |
|---|---|
| `workOrders` | A nonempty list of distinct identifiers from `R0040`, `R003F`, `R0035`, `R002F`; only those observation lanes run, in the existing canonical order. R0035 defaults to both timing and capture. |
| `evidenceRetention` | A boolean, default `false`. When `true`, selected R0040/R0035 lanes execute their exact original source through the reviewed supplemental wrappers. R003F/R002F commands are unchanged. |
| `r0035` | Optional dictionary with `guard: default` or `off`, `scope: all` or `preview-members`, and `mode: both`, `timing` or `capture`. Defaults preserve the original commands. Explicit controls require selected R0035 observations. Unknown fields and values are rejected. |
| `r003fHarness` | `published` (the original recipe, default) or `corrected-b0` (source-pinned MIME correction and full-UI admission). The latter requires selected R003F observations and separately admitted helper preparation. |
| `r0040Mode` | `options` (unchanged nine-option default) or `capture` (only reviewed Chromium/bday/moderate/M1/common on genuine main). Capture requires selected R0040, separate guarded preparation and its final-state wrapper. |

Unknown, duplicate, empty or malformed selections are rejected. R002F selection
must agree with `r002f.enabled` in both directions. When `workOrders` is absent,
the previous population is retained: R0040, R003F, R0035, plus R002F when enabled.
The initial campaign had four work orders and five command rows; the current
follow-up has three work orders and three command rows.
The selection, retention mode, diagnostic controls and every argument remain in private
receipts. Selection limits observations; the existing common source preparation
and original star-plan guards still run. R002F preparation remains conditional
on its enabled/selected state.

R0040 capture preparation is also conditional. The workflow acquires all six
historical helper/model/profile inputs and three reviewed preflight documents;
the research checkout already includes the required two complete patches and
12 declared inputs. Both actual preparation-entry exit zero and successful
guarded-recipe child receipts are required. The planner invokes the reviewed
read-only source guard on all six patched historical files, 12 research inputs,
116 generated members and 177 main runtime files. An incomplete optional rain
preparation blocks only that selected lane. Original patch receipts and partial
logs remain under private capture; disposable source remains under `work`.
The native wrapper repeats source admission before any original driver or
Playwright import. Exact commands and paths are in [LANES.md](LANES.md).

The guard-disabled diagnostic adds only `r35guard=off` to both experimental
arms. This existing lab switch removes both guard suspension and the guard's
gain ramp; it cannot isolate those two effects. Main, the shared lab, amplitude,
glass, margin, the 15-second dark/normal/ordinary-clock trial, source identity,
active producer predicate and original 100 ms cadence admission are unchanged.
Selecting `preview-members` changes that existing scope flag symmetrically; it
is a diagnostic population, not an accepted production cutoff. A timing-only
campaign omits capture deliberately, and a capture-only campaign has no phantom
timing dependency. Missing selected rows still become incomplete observations.
None of these controls fixes or erases the original failures, adopts a guard
policy, or supplies performance acceptance.

The original lunar HTTP helper does not serve CSS with its proper MIME type.
The earlier raw B0 receipt remains `MEASURED`, with a separate derived
`INCOMPLETE` disposition for full-widget harness faithfulness. Corrected B0
uses fresh disposable helpers whose exact inputs, guarded transformations and
outputs are bound by a reviewed deterministic materialization receipt. Product
and stylesheet bytes are unchanged. The planner rechecks every helper and the
actual preparation process status, then binds the native report to that exact
harness, engine/DPR, main index and four-capture population. Both UI observations
per capture must be retained; the pinned driver performs the full UI predicate
checks after every unchanged original physical assertion. Original Andon and
isolation precedence remain intact. Failed optional materialization blocks only
R003F and retains its private receipts/streams. See [R003F-HARNESS.md](R003F-HARNESS.md).

Instrumented lanes retain separate fresh `<lane-id>-retention` directories
beside the original outputs. Their unchanged result paths, kinds, admission
criteria and actual process statuses remain authoritative. The supplemental
journals cannot stand in for an absent original report. Serialization, hashing,
fsync and copying affect timing and capture; these observations are explicitly
marked instrumented and cannot be treated as original performance measurements.
See [EVIDENCE_RETENTION.md](EVIDENCE_RETENTION.md) for source pins, direct native
CLIs, partial-evidence interpretation and acquisition limits.

R002F preparation is optional and separate from common preparation. It uses
`r002f_prepare.py` and the exact reviewed probe described in [R002F.md](R002F.md).
Both immutable sparse checkouts include the exact R002B Pages preflight receipt.
R002F disposable source stays under `work/r002f-prepared`; its command streams,
build receipt and individual builder logs are copied under private capture.
An unsuccessful process, missing receipt or changed generated byte blocks that
lane as `NOT_RUN` with preparation `INCOMPLETE`. The other prepared recipes still
run. Any selected lane omitted from the plan receives an explicit missing-lane
`NOT_RUN` result with preparation `INCOMPLETE`, including every selected R0035 row.
Duplicate, wrong-identity or unselected command rows are rejected before lane
execution. Deliberately unselected work orders are recorded in the campaign
selection; they are not counted as missing observations. A later campaign can
therefore omit a workstream stopped by an earlier Andon while continuing the
selected independent observations. Earlier records are retained unchanged.
The disposable main arm is a detached sparse Git worktree using the admitted
baseline object database. This avoids a clone transport requesting omitted
archive objects after network isolation, while preserving actual HEAD, tree and
clean-status checks. Source bytes are rechecked after preparation.
The R003F runtime subset is copied from those acquired files only after matching
every body and mode to its HEAD blob. This is recorded as a verified runtime
subset, not as a `git archive` invocation; it needs no omitted archive objects.

## Isolation and private output

Dependency acquisition completes before observation. The Node lock derives its
exact Playwright/core 1.62.1 and pngjs 7.0.0 integrities from the reviewed repository
receipts. Four Python wheels are pinned by actual SHA-256, independently compared
with their PyPI release metadata; `dependency-provenance.json` records the sources.
No package lifecycle scripts are enabled. Managed browser descriptors and actual
binary digests are retained in the private acquisition receipt.

Every source-preparation or observation phase runs in a fresh network/PID namespace.
The trusted wrapper enables only loopback, drops all capability sets, real/effective/
saved root identity and supplementary groups, enables no-new-privileges and clears
the inherited environment. It does not repurpose HOME or CODEX_HOME. Explicit task
paths hold caches, temporary files and browser installs. No private recipient key
is supplied to Actions.

Before a recipe runs, the process checks its namespace, interface/route census,
privilege state and a real refused TEST-NET socket. A real pinned Chromium launch
with `chromiumSandbox: true` then reads a loopback marker, attempts a TEST-NET
navigation without any route stub/proxy/DNS override, requires routing failure,
and reads the loopback marker again. The existing R003F sandbox, refusing proxy,
WebSocket guard and assertions remain intact. One browser driver runs at a time.
The separate control, R003F and R002F opt into the Chromium renderer sandbox. The original
R0040 and R0035 recipes retain their default launch settings; the control does not
prove those recipe renderers are sandboxed. Their common isolation boundary is the
verified network/PID namespace and privilege/environment drop described above.

All recipe output, source/build logs, screenshots, measurements, request ledgers
where the original recipe produces them, and diagnostic failures remain below a
mode-700 capture directory. The default original R0040/R0035 recipes do not persist the
same detailed per-request ledger as R003F; the outer boundary receipt does not
claim that missing inner evidence. Optional instrumented wrappers retain actions
seen by the original context route, with the limits stated in the retention
document. Any isolation failure ends all observation;
R003F Andon ends that workstream's proposal progression. Other failed admissions
are preserved and do not erase independently obtainable lanes.

`envelope.py` seals the private directory to `capture.p7m` plus `envelope.json`.
Only those two files are admitted to the public-repository Actions artifact, for
seven days. Authenticated repository/run/artifact retrieval supplies sender
provenance; recipient encryption alone does not authenticate the sender. Recover
artifacts promptly and validate/decrypt privately using the separately held key.

## Result interpretation

`observation.json` keeps per-lane process and semantic status distinct. A zero exit
from R0035 is insufficient: every required trial must actually be admitted with a
passed qualification. A failed admission stays `FAIL`; missing acquisition stays
`INCOMPLETE`. Abnormal namespace completion overrides any inner pass, retains both
records and stops all later lanes as `ISOLATION_UNCONFIRMED` unless an actual
isolation failure is already recorded.

The revised R0040 capture has the separate status
`ADMITTED_FOR_OFFLINE_VERIFICATION`, requiring actual child exit zero, its raw
report and the exact final wrapper receipt after cleanup. Native qualification
remains `NOT_VERIFIED`; `OBSERVED` is an acquisition summary and cannot claim
that the lossless verifier passed. Missing/partial custody remains incomplete,
and original or late acquisition failures remain failed. After private retrieval,
run the unchanged `lossless_pack.py cell` with `pins-revised.json` in the existing
Pillow/cryptography environment. No package is added to hosted acquisition and
no original frame-count, gap, average-rate or pixel gate changes.

For an instrumented R0040/R0035 child, exit `86` instead records
`EXTERNAL_CONTINUATION_VETOED`: the wrapper prevented an attempted external
continuation before the real continue action. This stops all later observations
and is not evidence of an actual network escape. After writing that admitted
inner receipt, the namespace coordinator completes normally; the receipt keeps
the child's actual exit `86` and `stopAll: true`. Actual outer exit `86`, timeout,
abnormal completion or a missing receipt still overrides the inner result with
the appropriate isolation failure/unconfirmed status. A readable final journal
event never overrides a nonzero actual recipe exit, including a terminal fsync
or close failure.

R002F additionally requires its report protocol, observer/source identities,
configured engine/DPR/rounds/section, every expected prayer scenario/round and
both expected preview arms before `PASS`. Its original `FAIL`, `INCOMPLETE` and
`INCONCLUSIVE` remain distinct; a legitimate inconclusive discriminator does not
become an isolation failure. The native lane is bounded to 900 seconds with
60-second page setup waits. The common observation budget still applies, and
unreached lanes are retained as `NOT_RUN`.
R003F B0 `MEASURED` is a bounded baseline measurement. R0040's nine cells exercise
the stated native option assertions. None is a whole-work-order acceptance claim.
The original research gate `PASS_WITH_DECLARED_FAILURES (10)`, activated R002F
244/248 Moon outcome, and R0040 original cover 85/86 remain unchanged.

Hosted Linux/headless observations do not prove physical-device performance,
display presentation cadence, human naturalness/recognition or owner approval.
Failed and missing scenes are retained as failed or incomplete. After receiving
the first campaign, use the actual findings to acquire meaningful remaining
engine, DPR, motion and lifecycle observations; the pilot is not a stopping gate.

## Local controls

Run the envelope, isolation and lane controls with the repository's registered
test commands. Native recipes require the reviewed Linux namespace launcher and
installed managed engines. A host without those facilities may run offline
controls, but cannot report a native result. The ordinary qualification workflow,
product source, generated deliveries, vendor and frozen V1 are unchanged.
