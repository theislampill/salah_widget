# Hosted native research observations

This opt-in branch runs private research observations for Salah Widget R002F-A2,
R0035, R0040 and R003F. The first campaign includes the three already published
recipes. It does not adopt a product candidate or supply owner/human acceptance.

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
The separate control and R003F opt into the Chromium renderer sandbox. The original
R0040 and R0035 recipes retain their default launch settings; the control does not
prove those recipe renderers are sandboxed. Their common isolation boundary is the
verified network/PID namespace and privilege/environment drop described above.

All recipe output, source/build logs, screenshots, measurements, request ledgers
where the original recipe produces them, and diagnostic failures remain below a
mode-700 capture directory. The original R0040/R0035 recipes do not persist the
same detailed per-request ledger as R003F; the outer boundary receipt does not
claim that missing inner evidence. Any isolation failure ends all observation;
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
